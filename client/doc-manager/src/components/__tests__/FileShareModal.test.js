// src/components/__tests__/FileShareModal.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MockAdapter from 'axios-mock-adapter';
import api from '../../api/client';
import FileShareModal from '../FileShareModal';

const mockAxios = new MockAdapter(api);

const mockFile = {
  id: 1,
  file_name: 'test-document.pdf',
  virtual_path: '/documents/test-document.pdf'
};

const defaultProps = {
  file: mockFile,
  isOpen: true,
  onClose: jest.fn(),
  onSuccess: jest.fn()
};

const renderModal = (props = {}) => {
  return render(<FileShareModal {...defaultProps} {...props} />);
};

describe('FileShareModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
  });

  test('does not render when isOpen is false', () => {
    renderModal({ isOpen: false });
    expect(screen.queryByText('Share File')).not.toBeInTheDocument();
  });

  test('renders modal with file information', () => {
    renderModal();

    expect(screen.getByText('Share File')).toBeInTheDocument();
    expect(screen.getByText(/Share "test-document.pdf" with another user/)).toBeInTheDocument();
    expect(screen.getByLabelText(/User Email/)).toBeInTheDocument();
  });

  test('renders permission options', () => {
    renderModal();

    expect(screen.getByText('View only')).toBeInTheDocument();
    expect(screen.getByText('Can edit')).toBeInTheDocument();
    expect(screen.getByText(/User can view and download the file/)).toBeInTheDocument();
    expect(screen.getByText(/User can view, download, and upload new versions/)).toBeInTheDocument();
  });

  test('handles successful file sharing', async () => {
    const user = userEvent.setup();
    const mockOnSuccess = jest.fn();
    const mockOnClose = jest.fn();

    mockAxios.onPost('/share/').reply(200, {
      message: 'File shared successfully',
      permissions: ['view']
    });

    renderModal({ onSuccess: mockOnSuccess, onClose: mockOnClose });

    await user.type(screen.getByLabelText(/User Email/), 'user@example.com');
    await user.click(screen.getByRole('button', { name: /Share File/ }));

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalledWith('File shared successfully');
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  test('handles sharing with edit permissions', async () => {
    const user = userEvent.setup();

    mockAxios.onPost('/share/').reply(200, {
      message: 'File shared with edit permissions',
      permissions: ['view', 'edit']
    });

    renderModal();

    await user.type(screen.getByLabelText(/User Email/), 'user@example.com');
    await user.click(screen.getByLabelText(/Can edit/));
    await user.click(screen.getByRole('button', { name: /Share File/ }));

    await waitFor(() => {
      expect(mockAxios.history.post[0].data).toContain('"can_edit":true');
    });
  });

  test('handles sharing error', async () => {
    const user = userEvent.setup();

    mockAxios.onPost('/share/').reply(404, {
      detail: 'User with this email not found'
    });

    renderModal();

    await user.type(screen.getByLabelText(/User Email/), 'notfound@example.com');
    await user.click(screen.getByRole('button', { name: /Share File/ }));

    await waitFor(() => {
      expect(screen.getByText(/User with this email not found/)).toBeInTheDocument();
    });
  });

  test('validates required email field', async () => {
    const user = userEvent.setup();
    renderModal();

    await user.click(screen.getByRole('button', { name: /Share File/ }));

    expect(screen.getByText(/Email is required/)).toBeInTheDocument();
  });

  test('shows loading state during sharing', async () => {
    const user = userEvent.setup();

    mockAxios.onPost('/share/').reply(() => {
      return new Promise(resolve => {
        setTimeout(() => resolve([200, { message: 'Success' }]), 100);
      });
    });

    renderModal();

    await user.type(screen.getByLabelText(/User Email/), 'user@example.com');
    await user.click(screen.getByRole('button', { name: /Share File/ }));

    expect(screen.getByText(/Sharing.../)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sharing.../ })).toBeDisabled();
  });

  test('closes modal when clicking outside', () => {
    const mockOnClose = jest.fn();
    renderModal({ onClose: mockOnClose });

    fireEvent.click(screen.getByRole('dialog').parentElement);
    expect(mockOnClose).toHaveBeenCalled();
  });

  test('closes modal when clicking close button', () => {
    const mockOnClose = jest.fn();
    renderModal({ onClose: mockOnClose });

    fireEvent.click(screen.getByRole('button', { name: '' })); // Close button
    expect(mockOnClose).toHaveBeenCalled();
  });

  test('closes modal when clicking cancel', () => {
    const mockOnClose = jest.fn();
    renderModal({ onClose: mockOnClose });

    fireEvent.click(screen.getByText('Cancel'));
    expect(mockOnClose).toHaveBeenCalled();
  });
});