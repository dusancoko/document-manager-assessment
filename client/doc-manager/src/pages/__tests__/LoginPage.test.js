// src/pages/__tests__/LoginPage.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import api from '../../api/client';
import LoginPage from '../LoginPage';
import { AuthContext } from '../../context/AuthContext';

const mockAxios = new MockAdapter(api);

const mockHistoryPush = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useHistory: () => ({
    push: mockHistoryPush
  })
}));

const renderLoginPage = (authValue = { token: null, login: jest.fn(), logout: jest.fn() }) => {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <LoginPage />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
  });

  test('renders login form correctly', () => {
    renderLoginPage();

    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByAltText(/propylon logo/i)).toBeInTheDocument();
  });

  test('redirects to home if already authenticated', () => {
    const mockAuthValue = {
      token: 'existing-token',
      login: jest.fn(),
      logout: jest.fn()
    };

    renderLoginPage(mockAuthValue);

    expect(mockHistoryPush).toHaveBeenCalledWith('/');
  });

  test('handles successful login', async () => {
    const user = userEvent.setup();
    const mockLogin = jest.fn();
    const authValue = { token: null, login: mockLogin, logout: jest.fn() };

    mockAxios.onPost('/token/').reply(200, {
      token: 'new-token',
      user_id: 1,
      email: 'test@example.com'
    });

    renderLoginPage(authValue);

    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('new-token');
      expect(mockHistoryPush).toHaveBeenCalledWith('/');
    });
  });

  test('handles login error', async () => {
    const user = userEvent.setup();
    const authValue = { token: null, login: jest.fn(), logout: jest.fn() };

    mockAxios.onPost('/token/').reply(401, {
      detail: 'Invalid credentials'
    });

    renderLoginPage(authValue);

    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  test('shows loading state during login', async () => {
    const user = userEvent.setup();
    const authValue = { token: null, login: jest.fn(), logout: jest.fn() };

    mockAxios.onPost('/token/').reply(() => {
      return new Promise(resolve => {
        setTimeout(() => resolve([200, { token: 'new-token' }]), 100);
      });
    });

    renderLoginPage(authValue);

    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(screen.getByText(/signing in/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
  });

  test('validates required fields', async () => {
    const user = userEvent.setup();
    renderLoginPage();

    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // HTML5 validation should prevent submission
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    expect(emailInput).toBeInvalid();
    expect(passwordInput).toBeInvalid();
  });
});