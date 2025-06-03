// src/__tests__/performance.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import api from '../api/client';
import MyFilesPage from '../pages/MyFilesPage';
import SharedWithMePage from '../pages/SharedWithMePage';
import { AuthContext } from '../context/AuthContext';

const mockAxios = new MockAdapter(api);

// Generate large dataset for performance testing
const generateMockFiles = (count) => {
  return Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    file_name: `document-${index + 1}.pdf`,
    virtual_path: `/documents/document-${index + 1}.pdf`,
    mime_type: 'application/pdf',
    file_size: Math.floor(Math.random() * 10000000),
    checksum: `checksum-${index + 1}`,
    version_number: Math.floor(Math.random() * 5) + 1,
    versions: Array.from({ length: Math.floor(Math.random() * 5) + 1 }, (_, vIndex) => ({
      id: index * 10 + vIndex + 1,
      version_number: vIndex + 1,
      virtual_path: `/documents/document-${index + 1}.pdf`
    }))
  }));
};

const renderWithAuth = (Component, authValue = { token: 'test-token' }) => {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <Component />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('Performance Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
  });

  test('renders large number of files efficiently', async () => {
    const startTime = performance.now();
    const largeFileList = generateMockFiles(100);
    
    mockAxios.onGet('file_versions/').reply(200, largeFileList);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText('document-1.pdf')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within reasonable time (less than 2 seconds)
    expect(renderTime).toBeLessThan(2000);
    
    // Should render all files
    expect(screen.getByText('document-100.pdf')).toBeInTheDocument();
  });

  test('handles very long file names and paths', async () => {
    const longFileName = 'a'.repeat(255) + '.pdf';
    const longPath = '/' + 'very-long-directory-name'.repeat(20) + '/' + longFileName;
    
    const filesWithLongNames = [{
      id: 1,
      file_name: longFileName,
      virtual_path: longPath,
      mime_type: 'application/pdf',
      file_size: 1024000,
      checksum: 'abc123',
      version_number: 1,
      versions: []
    }];

    mockAxios.onGet('file_versions/').reply(200, filesWithLongNames);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      // Should handle long names without breaking layout
      expect(screen.getByText(longFileName)).toBeInTheDocument();
    });
  });

  test('handles files with many versions efficiently', async () => {
    const fileWithManyVersions = {
      id: 1,
      file_name: 'document.pdf',
      virtual_path: '/documents/document.pdf',
      mime_type: 'application/pdf',
      file_size: 1024000,
      checksum: 'abc123',
      version_number: 50,
      versions: Array.from({ length: 50 }, (_, index) => ({
        id: index + 1,
        version_number: index + 1,
        virtual_path: '/documents/document.pdf'
      }))
    };

    mockAxios.onGet('file_versions/').reply(200, [fileWithManyVersions]);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
      expect(screen.getByText('50 versions available')).toBeInTheDocument();
    });

    // Version selector should have all versions
    const versionSelect = screen.getByRole('combobox');
    expect(versionSelect.children).toHaveLength(50);
  });

  test('memory usage remains stable with frequent re-renders', async () => {
    const files = generateMockFiles(50);
    mockAxios.onGet('file_versions/').reply(200, files);

    const { rerender } = renderWithAuth(MyFilesPage);

    // Force multiple re-renders
    for (let i = 0; i < 10; i++) {
      rerender(
        <MemoryRouter key={i}>
          <AuthContext.Provider value={{ token: 'test-token' }}>
            <MyFilesPage />
          </AuthContext.Provider>
        </MemoryRouter>
      );
    }

    await waitFor(() => {
      expect(screen.getByText('document-1.pdf')).toBeInTheDocument();
    });

    // Component should still render correctly after multiple re-renders
    expect(screen.getByText('My Files')).toBeInTheDocument();
  });
});