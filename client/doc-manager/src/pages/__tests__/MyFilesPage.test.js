// src/pages/__tests__/MyFilesPage.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import api from '../../api/client';
import MyFilesPage from '../MyFilesPage';
import { AuthContext } from '../../context/AuthContext';

const mockAxios = new MockAdapter(api);

const mockFiles = [
  {
    id: 1,
    file_name: 'document1.pdf',
    virtual_path: '/documents/document1.pdf',
    mime_type: 'application/pdf',
    file_size: 1024000,
    checksum: 'abc123def456',
    version_number: 2,
    versions: [
      { id: 1, version_number: 1, virtual_path: '/documents/document1.pdf' },
      { id: 2, version_number: 2, virtual_path: '/documents/document1.pdf' }
    ]
  },
  {
    id: 3,
    file_name: 'spreadsheet.xlsx',
    virtual_path: '/documents/spreadsheet.xlsx',
    mime_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    file_size: 512000,
    checksum: 'def456ghi789',
    version_number: 1,
    versions: [
      { id: 3, version_number: 1, virtual_path: '/documents/spreadsheet.xlsx' }
    ]
  }
];

const mockHistoryPush = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useHistory: () => ({
    push: mockHistoryPush
  })
}));

const renderMyFilesPage = (authValue = { token: 'test-token' }) => {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <MyFilesPage />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('MyFilesPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
    // Mock window.open
    Object.defineProperty(window, 'open', {
      writable: true,
      value: jest.fn()
    });
  });

  test('renders loading state initially', () => {
    mockAxios.onGet('file_versions/').reply(() => {
      return new Promise(() => {}); // Never resolves
    });

    renderMyFilesPage();
    expect(screen.getByText(/Loading your files/)).toBeInTheDocument();
  });

  test('renders empty state when no files', async () => {
    mockAxios.onGet('file_versions/').reply(200, []);

    renderMyFilesPage();

    await waitFor(() => {
      expect(screen.getByText(/No files uploaded yet/)).toBeInTheDocument();
      expect(screen.getByText(/Start by uploading your first document/)).toBeInTheDocument();
    });
  });

  test('renders files list correctly', async () => {
    mockAxios.onGet('file_versions/').reply(200, mockFiles);

    renderMyFilesPage();

    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
      expect(screen.getByText('spreadsheet.xlsx')).toBeInTheDocument();
      expect(screen.getByText(/1000 KB/)).toBeInTheDocument(); // File size formatting
      expect(screen.getByText(/500 KB/)).toBeInTheDocument();
    });
  });

  test('handles version selection change', async () => {
    const user = userEvent.setup();
    mockAxios.onGet('file_versions/').reply(200, mockFiles);

    renderMyFilesPage();

    await waitFor(() => {
      expect(screen.getByDisplayValue('Version 2 (Latest)')).toBeInTheDocument();
    });

    const versionSelect = screen.getAllByRole('combobox')[0];
    await user.selectOptions(versionSelect, '1');

    expect(versionSelect.value).toBe('1');
  });

  test('handles file download', async () => {
    const user = userEvent.setup();
    mockAxios.onGet('file_versions/').reply(200, mockFiles);

    renderMyFilesPage();

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

  test('handles upload new version navigation', async () => {
    const user = userEvent.setup();
    mockAxios.onGet('file_versions/').reply(200, mockFiles);

    renderMyFilesPage();

    await waitFor(() => {
      expect(screen.getAllByTitle(/Upload new version/)).toHaveLength(2);
    });

    const uploadButton = screen.getAllByTitle(/Upload new version/)[0];
    await user.click(uploadButton);

    expect(mockHistoryPush).toHaveBeenCalledWith({
      pathname: '/upload',
      state: {
        prefillVirtualPath: '/documents/document1.pdf',
        prefillFileName: 'document1.pdf'
      }
    });
  });

  test('handles compare versions navigation', async () => {
    const user = userEvent.setup();
    mockAxios.onGet('file_versions/').reply(200, mockFiles);

    renderMyFilesPage();

    await waitFor(() => {
      expect(screen.getAllByTitle(/Compare versions/)).toHaveLength(2);
    });

    const compareButton = screen.getAllByTitle(/Compare versions/)[0];
    await user.click(compareButton);

    expect(mockHistoryPush).toHaveBeenCalledWith('/compare/1');
  });

  test('disables compare button for files with only one version', async () => {
    mockAxios.onGet('file_versions/').reply(200, mockFiles);

    renderMyFilesPage();

    await waitFor(() => {
      const compareButtons = screen.getAllByTitle(/Compare versions/);
      expect(compareButtons[1]).toBeDisabled(); // Second file has only 1 version
    });
  });

  test('handles API error', async () => {
    mockAxios.onGet('file_versions/').reply(500);

    renderMyFilesPage();

    await waitFor(() => {
      expect(screen.getByText(/Could not load files/)).toBeInTheDocument();
    });
  });

  test('opens share modal when share button clicked', async () => {
    const user = userEvent.setup();
    mockAxios.onGet('file_versions/').reply(200, mockFiles);

    renderMyFilesPage();

    await waitFor(() => {
      expect(screen.getAllByTitle(/Share file/)).toHaveLength(2);
    });

    const shareButton = screen.getAllByTitle(/Share file/)[0];
    await user.click(shareButton);

    expect(screen.getByText('Share File')).toBeInTheDocument();
  });
});