// src/pages/__tests__/SharedWithMePage.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import api from '../../api/client';
import SharedWithMePage from '../SharedWithMePage';
import { AuthContext } from '../../context/AuthContext';

const mockAxios = new MockAdapter(api);

const mockSharedFiles = [
  {
    id: 1,
    file_name: 'shared-document.pdf',
    virtual_path: '/documents/shared-document.pdf',
    mime_type: 'application/pdf',
    file_size: 2048000,
    checksum: 'shared123',
    version_number: 3,
    owner_email: 'owner@example.com',
    permissions: ['view', 'edit'],
    versions: [
      { id: 1, version_number: 1, virtual_path: '/documents/shared-document.pdf' },
      { id: 2, version_number: 2, virtual_path: '/documents/shared-document.pdf' },
      { id: 3, version_number: 3, virtual_path: '/documents/shared-document.pdf' }
    ]
  },
  {
    id: 4,
    file_name: 'readonly-file.txt',
    virtual_path: '/documents/readonly-file.txt',
    mime_type: 'text/plain',
    file_size: 1024,
    checksum: 'readonly456',
    version_number: 1,
    owner_email: 'another@example.com',
    permissions: ['view'],
    versions: [
      { id: 4, version_number: 1, virtual_path: '/documents/readonly-file.txt' }
    ]
  }
];

const renderSharedWithMePage = (authValue = { token: 'test-token' }) => {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <SharedWithMePage />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('SharedWithMePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
    Object.defineProperty(window, 'open', {
      writable: true,
      value: jest.fn()
    });
  });

  test('renders page title correctly', () => {
    mockAxios.onGet('file_versions/shared-with-me/').reply(200, []);
    renderSharedWithMePage();
    
    expect(screen.getByText('Shared with me')).toBeInTheDocument();
  });

  test('renders empty state when no shared files', async () => {
    mockAxios.onGet('file_versions/shared-with-me/').reply(200, []);

    renderSharedWithMePage();

    await waitFor(() => {
      expect(screen.getByText(/No files shared with you/)).toBeInTheDocument();
      expect(screen.getByText(/Files that others share with you will appear here/)).toBeInTheDocument();
    });
  });

  test('renders shared files with owner information', async () => {
    mockAxios.onGet('file_versions/shared-with-me/').reply(200, mockSharedFiles);

    renderSharedWithMePage();

    await waitFor(() => {
      expect(screen.getByText('shared-document.pdf')).toBeInTheDocument();
      expect(screen.getByText('readonly-file.txt')).toBeInTheDocument();
      expect(screen.getByText(/Shared by: owner@example.com/)).toBeInTheDocument();
      expect(screen.getByText(/Shared by: another@example.com/)).toBeInTheDocument();
    });
  });

  test('displays permission badges correctly', async () => {
    mockAxios.onGet('file_versions/shared-with-me/').reply(200, mockSharedFiles);

    renderSharedWithMePage();

    await waitFor(() => {
      // First file has view and edit permissions
      const viewBadges = screen.getAllByText('View');
      const editBadges = screen.getAllByText('Edit');
      
      expect(viewBadges).toHaveLength(2); // Both files have view
      expect(editBadges).toHaveLength(1); // Only first file has edit
    });
  });

  test('shows edit button only for files with edit permission', async () => {
    mockAxios.onGet('file_versions/shared-with-me/').reply(200, mockSharedFiles);

    renderSharedWithMePage();

    await waitFor(() => {
      const uploadButtons = screen.getAllByTitle(/Upload new version/);
      expect(uploadButtons).toHaveLength(1); // Only first file allows editing
    });
  });

  test('shows download button for files with view permission', async () => {
    mockAxios.onGet('file_versions/shared-with-me/').reply(200, mockSharedFiles);

    renderSharedWithMePage();

    await waitFor(() => {
      const downloadButtons = screen.getAllByTitle(/Download version/);
      expect(downloadButtons).toHaveLength(2); // Both files allow viewing
    });
  });

  test('handles file download for shared files', async () => {
    const user = userEvent.setup();
    mockAxios.onGet('file_versions/shared-with-me/').reply(200, mockSharedFiles);

    renderSharedWithMePage();

    await waitFor(() => {
      expect(screen.getAllByTitle(/Download version/)).toHaveLength(2);
    });

    const downloadButton = screen.getAllByTitle(/Download version/)[0];
    await user.click(downloadButton);

    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining('/api/download/'),
      '_blank'
    );
  });

  test('handles API error', async () => {
    mockAxios.onGet('file_versions/shared-with-me/').reply(500);

    renderSharedWithMePage();

    await waitFor(() => {
      expect(screen.getByText(/Could not load shared files/)).toBeInTheDocument();
    });
  });
});
