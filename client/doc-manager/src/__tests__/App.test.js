// src/__tests__/App.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock all the page components
jest.mock('../pages/LoginPage', () => {
  return function LoginPage() {
    return <div data-testid="login-page">Login Page</div>;
  };
});

jest.mock('../pages/MyFilesPage', () => {
  return function MyFilesPage() {
    return <div data-testid="my-files-page">My Files Page</div>;
  };
});

jest.mock('../pages/SharedWithMePage', () => {
  return function SharedWithMePage() {
    return <div data-testid="shared-page">Shared Page</div>;
  };
});

jest.mock('../pages/UploadPage', () => {
  return function UploadPage() {
    return <div data-testid="upload-page">Upload Page</div>;
  };
});

jest.mock('../pages/FilePage', () => {
  return function FilePage() {
    return <div data-testid="file-page">File Page</div>;
  };
});

jest.mock('../pages/CompareVersionsPage', () => {
  return function CompareVersionsPage() {
    return <div data-testid="compare-page">Compare Page</div>;
  };
});

// Mock AuthContext
const mockAuthContext = {
  token: null,
  login: jest.fn(),
  logout: jest.fn()
};

jest.mock('../context/AuthContext', () => ({
  AuthProvider: ({ children }) => children,
  AuthContext: {
    Provider: ({ children }) => children
  }
}));

jest.mock('../context/PrivateRoute', () => {
  return function PrivateRoute({ Component }) {
    return <Component />;
  };
});

describe('App', () => {
  test('renders without crashing', () => {
    render(<App />);
    // App should render without throwing errors
  });
});
