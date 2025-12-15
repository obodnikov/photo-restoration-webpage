/**
 * Test utilities for React Testing Library
 *
 * Provides custom render functions and test helpers
 */

import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

/**
 * Custom render function that wraps components with providers
 */
export function renderWithRouter(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, {
    wrapper: ({ children }) => <BrowserRouter>{children}</BrowserRouter>,
    ...options,
  });
}

/**
 * Mock user for tests
 */
export const mockUser = {
  username: 'testuser',
};

/**
 * Mock valid JWT token (simplified for tests)
 */
export const mockToken = 'mock-jwt-token-for-testing';

/**
 * Mock expired JWT token
 */
export const mockExpiredToken = 'mock-expired-jwt-token';

/**
 * Mock login response
 */
export const mockLoginResponse = {
  access_token: mockToken,
  token_type: 'bearer',
  expires_in: 86400, // 24 hours in seconds
};

/**
 * Mock login response with Remember Me (7 days)
 */
export const mockLoginResponseRememberMe = {
  access_token: mockToken,
  token_type: 'bearer',
  expires_in: 604800, // 7 days in seconds
};

/**
 * Mock user response
 */
export const mockUserResponse = {
  username: mockUser.username,
};

/**
 * Mock token validate response
 */
export const mockTokenValidateResponse = {
  valid: true,
  username: mockUser.username,
};

/**
 * Wait for a specific amount of time
 */
export const wait = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Mock fetch for successful responses
 */
export function mockFetchSuccess<T>(data: T, status = 200) {
  return vi.fn(() =>
    Promise.resolve({
      ok: status >= 200 && status < 300,
      status,
      statusText: 'OK',
      json: () => Promise.resolve(data),
      headers: new Headers(),
      redirected: false,
      type: 'basic' as ResponseType,
      url: '',
      clone: vi.fn(),
      body: null,
      bodyUsed: false,
      arrayBuffer: vi.fn(),
      blob: vi.fn(),
      formData: vi.fn(),
      text: vi.fn(),
    } as Response)
  );
}

/**
 * Mock fetch for error responses
 */
export function mockFetchError(status = 500, message = 'Error') {
  return vi.fn(() =>
    Promise.resolve({
      ok: false,
      status,
      statusText: message,
      json: () => Promise.resolve({ detail: message }),
      headers: new Headers(),
      redirected: false,
      type: 'basic' as ResponseType,
      url: '',
      clone: vi.fn(),
      body: null,
      bodyUsed: false,
      arrayBuffer: vi.fn(),
      blob: vi.fn(),
      formData: vi.fn(),
      text: vi.fn(),
    } as Response)
  );
}

/**
 * Mock fetch for network error
 */
export function mockFetchNetworkError() {
  return vi.fn(() => Promise.reject(new Error('Network error')));
}

// Re-export testing library utilities
export * from '@testing-library/react';
import userEventLib from '@testing-library/user-event';
export const userEvent = userEventLib;
