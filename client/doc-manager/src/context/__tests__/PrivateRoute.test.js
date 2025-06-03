// src/context/__tests__/PrivateRoute.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PrivateRoute from '../PrivateRoute';
import { AuthContext } from '../AuthContext';

const TestComponent = () => <div data-testid="protected-content">Protected Content</div>;

const renderPrivateRoute = (token = null) => {
  const authValue = { token, login: jest.fn(), logout: jest.fn() };
  
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <PrivateRoute Component={TestComponent} />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('PrivateRoute', () => {
  test('renders component when user is authenticated', () => {
    renderPrivateRoute('test-token');
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });

  test('redirects to login when user is not authenticated', () => {
    renderPrivateRoute(null);
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });
});