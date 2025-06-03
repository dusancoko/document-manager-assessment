// src/pages/__tests__/CompareVersionsPage.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import api from '../../api/client';
import CompareVersionsPage from '../CompareVersionsPage';
import { AuthContext } from '../../context/AuthContext';

const mockAxios = new MockAdapter(api);

const mockFileData = {
  id: 1,
  file_name: 'document.txt',
  virtual_path: '/documents/document.txt',
  mime_type: 'text/plain',
  versions: [
    { id: 1, version_number: 1, virtual_path: '/documents/document.txt' },
    { id: 2, version_number: 2, virtual_path: '/documents/document.txt' },
    { id: 3, version_number: 3, virtual_path: '/documents/document.txt' }
  ]
};

const mockComparisonData = {
  left_file: {
    id: 1,
    name: 'document.txt',
    text: 'Original content line 1\nOriginal content line 2'
  },
  right_file: {
    id: 2,
    name: 'document.txt',
    text: 'Modified content line 1\nModified content line 2\nNew line added'
  }
};

const renderCompareVersionsPage = (fileId = '1', authValue = { token: 'test-token' }) => {
  return render(
    <MemoryRouter initialEntries={[`/compare/${fileId}`]}>
      <AuthContext.Provider value={authValue}>
        <CompareVersionsPage />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('CompareVersionsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
  });

  test('shows loading state while fetching file details', () => {
    mockAxios.onGet('file_versions/1/').reply(() => {
      return new Promise(() => {}); // Never resolves
    });

    renderCompareVersionsPage();
    
    expect(screen.getByText(/Loading file details/)).toBeInTheDocument();
  });

  test('renders file information correctly', async () => {
    mockAxios.onGet('file_versions/1/').reply(200, mockFileData);

    renderCompareVersionsPage();

    await waitFor(() => {
      expect(screen.getByText('Compare File Versions')).toBeInTheDocument();
      expect(screen.getByText('document.txt')).toBeInTheDocument();
      expect(screen.getByText('/documents/document.txt')).toBeInTheDocument();
      expect(screen.getByText('Type: text/plain')).toBeInTheDocument();
    });
  });

  test('renders version selectors with correct options', async () => {
    mockAxios.onGet('file_versions/1/').reply(200, mockFileData);

    renderCompareVersionsPage();

    await waitFor(() => {
      const leftSelect = screen.getByLabelText(/Left Version/);
      const rightSelect = screen.getByLabelText(/Right Version/);
      
      expect(leftSelect).toBeInTheDocument();
      expect(rightSelect).toBeInTheDocument();
      
      // Should have options for all versions
      expect(screen.getAllByText(/Version 1/)).toHaveLength(2);
      expect(screen.getAllByText(/Version 2/)).toHaveLength(2);
      expect(screen.getAllByText(/Version 3 \(Latest\)/)).toHaveLength(2);
    });
  });

  test('automatically compares latest and previous version by default', async () => {
    mockAxios.onGet('file_versions/1/').reply(200, mockFileData);
    mockAxios.onGet('/compare/').reply(200, mockComparisonData);

    renderCompareVersionsPage();

    await waitFor(() => {
      // Should automatically trigger comparison
      expect(mockAxios.history.get).toHaveLength(2); // File details + comparison
      expect(mockAxios.history.get[1].url).toContain('left_id=2&right_id=3');
    });
  });

  test('handles version selection change', async () => {
    const user = userEvent.setup();
    mockAxios.onGet('file_versions/1/').reply(200, mockFileData);
    mockAxios.onGet('/compare/').reply(200, mockComparisonData);

    renderCompareVersionsPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/Left Version/)).toBeInTheDocument();
    });

    const leftSelect = screen.getByLabelText(/Left Version/);
    await user.selectOptions(leftSelect, '1');

    await waitFor(() => {
      // Should trigger new comparison
      expect(mockAxios.history.get.filter(req => req.url.includes('/compare/'))).toHaveLength(2);
    });
  });

  test('renders diff viewer when comparison is successful', async () => {
    mockAxios.onGet('file_versions/1/').reply(200, mockFileData);
    mockAxios.onGet('/compare/').reply(200, mockComparisonData);

    renderCompareVersionsPage();

    await waitFor(() => {
      expect(screen.getByText('Version Comparison Results')).toBeInTheDocument();
      // ReactDiffViewer should be rendered (mocked in setup)
    });
  });

  test('shows error message for unsupported file types', async () => {
    const unsupportedFile = {
      ...mockFileData,
      mime_type: 'application/octet-stream'
    };
    
    mockAxios.onGet('file_versions/1/').reply(200, unsupportedFile);

    renderCompareVersionsPage();

    await waitFor(() => {
      expect(screen.getByText(/File type not supported for comparison/)).toBeInTheDocument();
      expect(screen.getByText(/application\/octet-stream/)).toBeInTheDocument();
    });
  });

  test('handles comparison API error', async () => {
    mockAxios.onGet('file_versions/1/').reply(200, mockFileData);
    mockAxios.onGet('/compare/').reply(500);

    renderCompareVersionsPage();

    await waitFor(() => {
      expect(screen.getByText(/Could not compare the selected versions/)).toBeInTheDocument();
    });
  });

  test('shows warning when no versions available', async () => {
    const noVersionsFile = { ...mockFileData, versions: [] };
    mockAxios.onGet('file_versions/1/').reply(200, noVersionsFile);

    renderCompareVersionsPage();

    await waitFor(() => {
      expect(screen.getByText(/No versions available for comparison/)).toBeInTheDocument();
    });
  });

  test('shows loading state during comparison', async () => {
    mockAxios.onGet('file_versions/1/').reply(200, mockFileData);
    mockAxios.onGet('/compare/').reply(() => {
      return new Promise(() => {}); // Never resolves
    });

    renderCompareVersionsPage();

    await waitFor(() => {
      expect(screen.getByText(/Comparing versions/)).toBeInTheDocument();
    });
  });
});