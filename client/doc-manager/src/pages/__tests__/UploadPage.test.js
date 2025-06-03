// src/pages/__tests__/UploadPage.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import api from '../../api/client';
import UploadPage from '../UploadPage';

const mockAxios = new MockAdapter(api);

const renderUploadPage = (initialState = {}) => {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/upload', state: initialState }]}>
      <UploadPage />
    </MemoryRouter>
  );
};

const createMockFile = (name = 'test.txt', type = 'text/plain') => {
  return new File(['test content'], name, { type });
};

describe('UploadPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
  });

  test('renders upload form correctly', () => {
    renderUploadPage();

    expect(screen.getByText('Upload File')).toBeInTheDocument();
    expect(screen.getByLabelText(/Select File/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Display Name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Virtual Path/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Upload File/ })).toBeInTheDocument();
  });

  test('shows prefill notification when state is provided', () => {
    renderUploadPage({
      prefillVirtualPath: '/documents/existing.pdf',
      prefillFileName: 'existing.pdf'
    });

    expect(screen.getByText(/Uploading new version for/)).toBeInTheDocument();
    expect(screen.getByText('/documents/existing.pdf')).toBeInTheDocument();
  });

  test('auto-populates display name when file is selected', async () => {
    const user = userEvent.setup();
    renderUploadPage();

    const fileInput = screen.getByLabelText(/Select File/);
    const file = createMockFile('my-document.pdf', 'application/pdf');

    await user.upload(fileInput, file);

    const displayNameInput = screen.getByLabelText(/Display Name/);
    expect(displayNameInput.value).toBe('my-document.pdf');
  });

  test('handles successful file upload', async () => {
    const user = userEvent.setup();
    
    mockAxios.onPost('/upload/').reply(201, {
      message: 'File uploaded',
      version: 2,
      checksum: 'abc123'
    });

    renderUploadPage();

    const fileInput = screen.getByLabelText(/Select File/);
    const file = createMockFile('test-document.pdf', 'application/pdf');
    
    await user.upload(fileInput, file);
    await user.type(screen.getByLabelText(/Virtual Path/), '/documents/test-document.pdf');
    await user.click(screen.getByRole('button', { name: /Upload File/ }));

    await waitFor(() => {
      expect(screen.getByText(/Upload successful! Version 2 created/)).toBeInTheDocument();
    });
  });

  test('handles upload error', async () => {
    const user = userEvent.setup();
    
    mockAxios.onPost('/upload/').reply(400, {
      detail: 'File too large'
    });

    renderUploadPage();

    const fileInput = screen.getByLabelText(/Select File/);
    const file = createMockFile('large-file.pdf', 'application/pdf');
    
    await user.upload(fileInput, file);
    await user.type(screen.getByLabelText(/Virtual Path/), '/documents/large-file.pdf');
    await user.click(screen.getByRole('button', { name: /Upload File/ }));

    await waitFor(() => {
      expect(screen.getByText(/File too large/)).toBeInTheDocument();
    });
  });

  test('shows upload progress', async () => {
    const user = userEvent.setup();
    
    let progressCallback;
    mockAxios.onPost('/upload/').reply((config) => {
      progressCallback = config.onUploadProgress;
      return new Promise(resolve => {
        setTimeout(() => {
          // Simulate progress
          progressCallback({ loaded: 50, total: 100 });
          setTimeout(() => {
            progressCallback({ loaded: 100, total: 100 });
            resolve([201, { message: 'Upload complete', version: 1 }]);
          }, 50);
        }, 50);
      });
    });

    renderUploadPage();

    const fileInput = screen.getByLabelText(/Select File/);
    const file = createMockFile('test.pdf', 'application/pdf');
    
    await user.upload(fileInput, file);
    await user.type(screen.getByLabelText(/Virtual Path/), '/documents/test.pdf');
    await user.click(screen.getByRole('button', { name: /Upload File/ }));

    // Should show progress
    await waitFor(() => {
      expect(screen.getByText(/Upload Progress/)).toBeInTheDocument();
    });
  });

  test('disables form during upload', async () => {
    const user = userEvent.setup();
    
    mockAxios.onPost('/upload/').reply(() => {
      return new Promise(() => {}); // Never resolves
    });

    renderUploadPage();

    const fileInput = screen.getByLabelText(/Select File/);
    const file = createMockFile('test.pdf', 'application/pdf');
    
    await user.upload(fileInput, file);
    await user.type(screen.getByLabelText(/Virtual Path/), '/documents/test.pdf');
    await user.click(screen.getByRole('button', { name: /Upload File/ }));

    await waitFor(() => {
      expect(screen.getByText(/Uploading.../)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Uploading.../ })).toBeDisabled();
    });
  });
});