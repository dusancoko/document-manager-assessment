// src/__tests__/integration.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import api from '../api/client';
import App from '../App';

const mockAxios = new MockAdapter(api);

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock window.open
Object.defineProperty(window, 'open', {
  writable: true,
  value: jest.fn()
});

describe('Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
    localStorageMock.getItem.mockReturnValue(null);
  });

  test('complete login to file listing flow', async () => {
    const user = userEvent.setup();
    
    // Mock login API call
    mockAxios.onPost('/token/').reply(200, {
      token: 'test-token',
      user_id: 1,
      email: 'test@example.com'
    });

    // Mock files API call
    mockAxios.onGet('file_versions/').reply(200, [
      {
        id: 1,
        file_name: 'test-document.pdf',
        virtual_path: '/documents/test-document.pdf',
        mime_type: 'application/pdf',
        file_size: 1024000,
        checksum: 'abc123',
        version_number: 1,
        versions: [
          { id: 1, version_number: 1, virtual_path: '/documents/test-document.pdf' }
        ]
      }
    ]);

    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );

    // Should start at login page
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();

    // Fill out login form
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Should navigate to files page and show files
    await waitFor(() => {
      expect(screen.getByText('My Files')).toBeInTheDocument();
      expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    });

    // Verify localStorage was called to store token
    expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'test-token');
  });

  test('file upload workflow', async () => {
    const user = userEvent.setup();
    
    // Start with authenticated user
    localStorageMock.getItem.mockReturnValue('test-token');
    
    // Mock upload API call
    mockAxios.onPost('/upload/').reply(201, {
      message: 'File uploaded',
      version: 1,
      checksum: 'abc123'
    });

    render(
      <MemoryRouter initialEntries={['/upload']}>
        <App />
      </MemoryRouter>
    );

    // Should be on upload page
    expect(screen.getByText('Upload File')).toBeInTheDocument();

    // Create and upload a file
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/Select File/);
    
    await user.upload(fileInput, file);
    await user.type(screen.getByLabelText(/Virtual Path/), '/documents/test.txt');
    await user.click(screen.getByRole('button', { name: /Upload File/ }));

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText(/Upload successful! Version 1 created/)).toBeInTheDocument();
    });
  });

  test('file sharing workflow', async () => {
    const user = userEvent.setup();
    
    localStorageMock.getItem.mockReturnValue('test-token');
    
    // Mock files list
    mockAxios.onGet('file_versions/').reply(200, [
      {
        id: 1,
        file_name: 'document.pdf',
        virtual_path: '/documents/document.pdf',
        mime_type: 'application/pdf',
        file_size: 1024000,
        checksum: 'abc123',
        version_number: 1,
        versions: []
      }
    ]);

    // Mock share API call
    mockAxios.onPost('/share/').reply(200, {
      message: 'File shared successfully',
      permissions: ['view']
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    // Wait for files to load
    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });

    // Click share button
    const shareButton = screen.getByTitle(/Share file/);
    await user.click(shareButton);

    // Should open share modal
    expect(screen.getByText('Share File')).toBeInTheDocument();

    // Fill out share form
    await user.type(screen.getByLabelText(/User Email/), 'colleague@example.com');
    await user.click(screen.getByRole('button', { name: /Share File/ }));

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText(/File shared successfully/)).toBeInTheDocument();
    });
  });

  test('navigation between pages', async () => {
    const user = userEvent.setup();
    
    localStorageMock.getItem.mockReturnValue('test-token');
    
    // Mock API calls for different pages
    mockAxios.onGet('file_versions/').reply(200, []);
    mockAxios.onGet('file_versions/shared-with-me/').reply(200, []);

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    // Should start on My Files page
    await waitFor(() => {
      expect(screen.getByText('My Files')).toBeInTheDocument();
    });

    // Navigate to Shared page
    const sharedLink = screen.getByText('Shared with me');
    await user.click(sharedLink);

    await waitFor(() => {
      expect(screen.getByText(/No files shared with you/)).toBeInTheDocument();
    });

    // Navigate to Upload page
    const uploadLink = screen.getByText('Upload');
    await user.click(uploadLink);

    await waitFor(() => {
      expect(screen.getByText('Upload File')).toBeInTheDocument();
    });

    // Navigate back to My Files
    const myFilesLink = screen.getByText('My Files');
    await user.click(myFilesLink);

    await waitFor(() => {
      expect(screen.getByText(/No files uploaded yet/)).toBeInTheDocument();
    });
  });

  test('logout functionality', async () => {
    const user = userEvent.setup();
    
    localStorageMock.getItem.mockReturnValue('test-token');
    mockAxios.onGet('file_versions/').reply(200, []);

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    // Should be authenticated and on files page
    await waitFor(() => {
      expect(screen.getByText('My Files')).toBeInTheDocument();
    });

    // Click logout
    const logoutButton = screen.getByText('Logout');
    await user.click(logoutButton);

    // Should redirect to login and remove token
    await waitFor(() => {
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });

    expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
  });
});