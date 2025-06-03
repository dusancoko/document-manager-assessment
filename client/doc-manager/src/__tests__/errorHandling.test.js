// src/__tests__/errorHandling.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import api from '../api/client';
import MyFilesPage from '../pages/MyFilesPage';
import UploadPage from '../pages/UploadPage';
import { AuthContext } from '../context/AuthContext';

const mockAxios = new MockAdapter(api);

const renderWithAuth = (Component, authValue = { token: 'test-token' }) => {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <Component />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('Error Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
    // Suppress console.error for these tests
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    console.error.mockRestore();
  });

  test('handles network errors gracefully', async () => {
    mockAxios.onGet('file_versions/').networkError();

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText(/Could not load files/)).toBeInTheDocument();
    });
  });

  test('handles 401 unauthorized errors', async () => {
    mockAxios.onGet('file_versions/').reply(401, {
      detail: 'Invalid authentication credentials'
    });

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText(/Could not load files/)).toBeInTheDocument();
    });
  });

  test('handles 403 forbidden errors', async () => {
    mockAxios.onGet('file_versions/').reply(403, {
      detail: 'You do not have permission to perform this action'
    });

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText(/Could not load files/)).toBeInTheDocument();
    });
  });

  test('handles 500 server errors', async () => {
    mockAxios.onGet('file_versions/').reply(500, {
      detail: 'Internal server error'
    });

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText(/Could not load files/)).toBeInTheDocument();
    });
  });

  test('handles upload timeout errors', async () => {
    const user = userEvent.setup();
    
    mockAxios.onPost('/upload/').timeout();

    renderWithAuth(UploadPage);

    const fileInput = screen.getByLabelText(/Select File/);
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    
    await user.upload(fileInput, file);
    await user.type(screen.getByLabelText(/Virtual Path/), '/test.txt');
    await user.click(screen.getByRole('button', { name: /Upload File/ }));

    await waitFor(() => {
      expect(screen.getByText(/timeout/i)).toBeInTheDocument();
    });
  });

  test('handles malformed API responses', async () => {
    mockAxios.onGet('file_versions/').reply(200, 'invalid json');

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText(/Could not load files/)).toBeInTheDocument();
    });
  });
});