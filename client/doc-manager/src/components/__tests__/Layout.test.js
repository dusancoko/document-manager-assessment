// src/components/__tests__/Layout.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from '../Layout';
import { AuthContext } from '../../context/AuthContext';

const mockHistoryPush = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useHistory: () => ({
    push: mockHistoryPush
  })
}));

const renderLayout = (pathname = '/', authValue = { logout: jest.fn() }) => {
  return render(
    <MemoryRouter initialEntries={[pathname]}>
      <AuthContext.Provider value={authValue}>
        <Layout>
          <div data-testid="children">Test Content</div>
        </Layout>
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('Layout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders navigation with correct links', () => {
    renderLayout();

    expect(screen.getByText('My Files')).toBeInTheDocument();
    expect(screen.getByText('Shared with me')).toBeInTheDocument();
    expect(screen.getByText('Upload')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  test('renders children content', () => {
    renderLayout();
    expect(screen.getByTestId('children')).toBeInTheDocument();
  });

  test('highlights active navigation link', () => {
    renderLayout('/shared');
    
    const sharedLink = screen.getByText('Shared with me');
    expect(sharedLink).toHaveClass('active');
    
    const myFilesLink = screen.getByText('My Files');
    expect(myFilesLink).not.toHaveClass('active');
  });

  test('handles logout click', () => {
    const mockLogout = jest.fn();
    renderLayout('/', { logout: mockLogout });

    fireEvent.click(screen.getByText('Logout'));

    expect(mockLogout).toHaveBeenCalled();
    expect(mockHistoryPush).toHaveBeenCalledWith('/login');
  });

  test('renders footer with current year', () => {
    renderLayout();
    expect(screen.getByText(/© 2024 Propylon Document Manager/)).toBeInTheDocument();
  });

  test('renders Propylon logo', () => {
    renderLayout();
    expect(screen.getByAltText('Propylon Logo')).toBeInTheDocument();
  });
});
