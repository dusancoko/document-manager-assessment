import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { AuthProvider, AuthContext } from '../AuthContext';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

const TestComponent = () => {
  const { token, login, logout } = React.useContext(AuthContext);
  
  return (
    <div>
      <span data-testid="token">{token || 'no-token'}</span>
      <button data-testid="login" onClick={() => login('test-token')}>
        Login
      </button>
      <button data-testid="logout" onClick={logout}>
        Logout
      </button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('provides initial token from localStorage', () => {
    localStorageMock.getItem.mockReturnValue('existing-token');
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('token')).toHaveTextContent('existing-token');
    expect(localStorageMock.getItem).toHaveBeenCalledWith('token');
  });

  test('provides null token when localStorage is empty', () => {
    localStorageMock.getItem.mockReturnValue(null);
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('token')).toHaveTextContent('no-token');
  });

  test('login sets token in state and localStorage', () => {
    localStorageMock.getItem.mockReturnValue(null);
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    act(() => {
      screen.getByTestId('login').click();
    });

    expect(screen.getByTestId('token')).toHaveTextContent('test-token');
    expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'test-token');
  });

  test('logout removes token from state and localStorage', () => {
    localStorageMock.getItem.mockReturnValue('test-token');
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    act(() => {
      screen.getByTestId('logout').click();
    });

    expect(screen.getByTestId('token')).toHaveTextContent('no-token');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
  });
});