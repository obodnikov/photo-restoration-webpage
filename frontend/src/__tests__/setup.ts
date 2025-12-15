/**
 * Test setup for Vitest
 *
 * This file runs before all tests and sets up the testing environment:
 * - Configures @testing-library/jest-dom matchers
 * - Mocks global objects (localStorage, fetch, etc.)
 * - Sets up test utilities
 */

import '@testing-library/jest-dom';
import { afterEach, beforeEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
afterEach(() => {
  cleanup();
  localStorage.clear();
  sessionStorage.clear();
});

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

Object.defineProperty(window, 'sessionStorage', {
  value: localStorageMock,
});

// Mock window.location
delete (window as any).location;
window.location = {
  ...window.location,
  href: '',
  pathname: '/',
  search: '',
  hash: '',
  assign: vi.fn(),
  reload: vi.fn(),
  replace: vi.fn(),
};

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: vi.fn(),
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  // Keep error for debugging
  error: console.error,
};

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks();
});
