// src/api/__tests__/client.test.js
import MockAdapter from 'axios-mock-adapter';
import api from '../client';

const mockAxios = new MockAdapter(api);

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
global.localStorage = localStorageMock;

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.reset();
  });

  test('includes auth token in request headers when available', async () => {
    localStorageMock.getItem.mockReturnValue('test-token');
    mockAxios.onGet('/test').reply(200, { success: true });

    await api.get('/test');

    expect(mockAxios.history.get[0].headers.Authorization).toBe('Token test-token');
  });

  test('does not include auth header when token is not available', async () => {
    localStorageMock.getItem.mockReturnValue(null);
    mockAxios.onGet('/test').reply(200, { success: true });

    await api.get('/test');

    expect(mockAxios.history.get[0].headers.Authorization).toBeUndefined();
  });

  test('uses correct base URL', () => {
    expect(api.defaults.baseURL).toBe('http://127.0.0.1:8001/api');
  });
});