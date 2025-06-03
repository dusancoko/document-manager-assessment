// src/__tests__/edgeCases.test.js
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import api from '../api/client';
import MyFilesPage from '../pages/MyFilesPage';
import UploadPage from '../pages/UploadPage';
import CompareVersionsPage from '../pages/CompareVersionsPage';
import FileShareModal from '../components/FileShareModal';
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

describe('Edge Cases', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
  });

  test('handles files with zero byte size', async () => {
    const emptyFile = {
      id: 1,
      file_name: 'empty.txt',
      virtual_path: '/documents/empty.txt',
      mime_type: 'text/plain',
      file_size: 0,
      checksum: 'emptyfile',
      version_number: 1,
      versions: []
    };

    mockAxios.onGet('file_versions/').reply(200, [emptyFile]);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText('empty.txt')).toBeInTheDocument();
      expect(screen.getByText('0 Bytes')).toBeInTheDocument();
    });
  });

  test('handles files with negative size (data corruption)', async () => {
    const corruptedFile = {
      id: 1,
      file_name: 'corrupted.pdf',
      virtual_path: '/documents/corrupted.pdf',
      mime_type: 'application/pdf',
      file_size: -1,
      checksum: 'corrupted',
      version_number: 1,
      versions: []
    };

    mockAxios.onGet('file_versions/').reply(200, [corruptedFile]);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText('corrupted.pdf')).toBeInTheDocument();
      // Should handle negative size gracefully
    });
  });

  test('handles files with null or undefined properties', async () => {
    const incompleteFile = {
      id: 1,
      file_name: 'incomplete.txt',
      virtual_path: '/documents/incomplete.txt',
      mime_type: null,
      file_size: undefined,
      checksum: '',
      version_number: 1,
      versions: null
    };

    mockAxios.onGet('file_versions/').reply(200, [incompleteFile]);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText('incomplete.txt')).toBeInTheDocument();
      // Should not crash despite null/undefined values
    });
  });

  test('handles special characters in file names and paths', async () => {
    const specialCharFile = {
      id: 1,
      file_name: 'file with spaces & special chars!@#$%^&*()_+.pdf',
      virtual_path: '/documents/special chars & symbols/file with spaces & special chars!@#$%^&*()_+.pdf',
      mime_type: 'application/pdf',
      file_size: 1024,
      checksum: 'special123',
      version_number: 1,
      versions: []
    };

    mockAxios.onGet('file_versions/').reply(200, [specialCharFile]);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText('file with spaces & special chars!@#$%^&*()_+.pdf')).toBeInTheDocument();
    });
  });

  test('handles Unicode characters in file names', async () => {
    const unicodeFile = {
      id: 1,
      file_name: '测试文档.pdf',
      virtual_path: '/documents/测试文档.pdf',
      mime_type: 'application/pdf',
      file_size: 1024,
      checksum: 'unicode123',
      version_number: 1,
      versions: []
    };

    mockAxios.onGet('file_versions/').reply(200, [unicodeFile]);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText('测试文档.pdf')).toBeInTheDocument();
    });
  });

  test('handles extremely large file sizes', async () => {
    const largeFile = {
      id: 1,
      file_name: 'huge-file.zip',
      virtual_path: '/documents/huge-file.zip',
      mime_type: 'application/zip',
      file_size: 999999999999, // Nearly 1TB
      checksum: 'huge123',
      version_number: 1,
      versions: []
    };

    mockAxios.onGet('file_versions/').reply(200, [largeFile]);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText('huge-file.zip')).toBeInTheDocument();
      expect(screen.getByText(/TB/)).toBeInTheDocument(); // Should show in TB
    });
  });

  test('handles upload of file with same name but different content', async () => {
    const user = userEvent.setup();
    
    mockAxios.onPost('/upload/').reply(201, {
      message: 'File uploaded',
      version: 2,
      checksum: 'differentcontent123'
    });

    renderWithAuth(UploadPage);

    const fileInput = screen.getByLabelText(/Select File/);
    const file = new File(['different content'], 'document.txt', { type: 'text/plain' });
    
    await user.upload(fileInput, file);
    await user.type(screen.getByLabelText(/Virtual Path/), '/documents/document.txt');
    await user.click(screen.getByRole('button', { name: /Upload File/ }));

    await waitFor(() => {
      expect(screen.getByText(/Upload successful! Version 2 created/)).toBeInTheDocument();
    });
  });

  test('handles rapid successive uploads', async () => {
    const user = userEvent.setup();
    
    let uploadCount = 0;
    mockAxios.onPost('/upload/').reply(() => {
      uploadCount++;
      return [201, { message: 'File uploaded', version: uploadCount, checksum: `upload${uploadCount}` }];
    });

    renderWithAuth(UploadPage);

    // Simulate rapid uploads
    for (let i = 0; i < 3; i++) {
      const fileInput = screen.getByLabelText(/Select File/);
      const file = new File([`content ${i}`], `file${i}.txt`, { type: 'text/plain' });
      
      await user.upload(fileInput, file);
      await user.clear(screen.getByLabelText(/Virtual Path/));
      await user.type(screen.getByLabelText(/Virtual Path/), `/documents/file${i}.txt`);
      
      // Don't wait for completion before starting next upload
      user.click(screen.getByRole('button', { name: /Upload File/ }));
    }

    // All uploads should eventually complete
    await waitFor(() => {
      expect(uploadCount).toBe(3);
    }, { timeout: 5000 });
  });

  test('handles comparison of identical files', async () => {
    const fileData = {
      id: 1,
      file_name: 'document.txt',
      mime_type: 'text/plain',
      versions: [
        { id: 1, version_number: 1 },
        { id: 2, version_number: 2 }
      ]
    };

    const identicalComparison = {
      left_file: { id: 1, name: 'document.txt', text: 'Same content' },
      right_file: { id: 2, name: 'document.txt', text: 'Same content' }
    };

    mockAxios.onGet('file_versions/1/').reply(200, fileData);
    mockAxios.onGet('/compare/').reply(200, identicalComparison);

    render(
      <MemoryRouter initialEntries={['/compare/1']}>
        <AuthContext.Provider value={{ token: 'test-token' }}>
          <CompareVersionsPage />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Version Comparison Results')).toBeInTheDocument();
    });
  });

  test('handles share modal with invalid email formats', async () => {
    const user = userEvent.setup();
    const mockFile = { id: 1, file_name: 'test.pdf' };

    render(
      <FileShareModal
        file={mockFile}
        isOpen={true}
        onClose={jest.fn()}
        onSuccess={jest.fn()}
      />
    );

    // Try invalid email formats
    const emailInput = screen.getByLabelText(/User Email/);
    
    await user.type(emailInput, 'invalid-email');
    await user.click(screen.getByRole('button', { name: /Share File/ }));

    // HTML5 validation should prevent submission
    expect(emailInput).toBeInvalid();
  });

  test('handles component unmounting during async operations', async () => {
    const user = userEvent.setup();
    
    // Mock a slow API response
    mockAxios.onGet('file_versions/').reply(() => {
      return new Promise(resolve => {
        setTimeout(() => resolve([200, []]), 1000);
      });
    });

    const { unmount } = renderWithAuth(MyFilesPage);

    // Unmount component before async operation completes
    setTimeout(() => unmount(), 100);

    // Should not cause any errors or warnings
    await new Promise(resolve => setTimeout(resolve, 1500));
  });

  test('handles window resize during file listing', async () => {
    mockAxios.onGet('file_versions/').reply(200, [
      {
        id: 1,
        file_name: 'responsive-test.pdf',
        virtual_path: '/documents/responsive-test.pdf',
        mime_type: 'application/pdf',
        file_size: 1024,
        checksum: 'responsive123',
        version_number: 1,
        versions: []
      }
    ]);

    renderWithAuth(MyFilesPage);

    await waitFor(() => {
      expect(screen.getByText('responsive-test.pdf')).toBeInTheDocument();
    });

    // Simulate window resize
    fireEvent(window, new Event('resize'));

    // Component should still be functional
    expect(screen.getByText('responsive-test.pdf')).toBeInTheDocument();
  });
});