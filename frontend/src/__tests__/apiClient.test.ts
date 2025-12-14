/**
 * Tests for API client
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import * as apiClient from '../services/apiClient';
import { useAuthStore } from '../services/authStore';
import {
  mockToken,
  mockUser,
  mockFetchSuccess,
  mockFetchError,
  mockFetchNetworkError,
} from '../test-utils';

describe('API Client', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    useAuthStore.getState().clearAuth();
    vi.clearAllMocks();
    // Reset window.location.href
    window.location.href = '';
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('Auto-inject auth token', () => {
    it('should include Authorization header when token exists', async () => {
      useAuthStore.getState().setAuth(mockToken, 86400, mockUser);

      const mockData = { message: 'success' };
      global.fetch = mockFetchSuccess(mockData);

      await apiClient.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${mockToken}`,
          }),
        })
      );
    });

    it('should redirect to login when no token exists for protected endpoint', async () => {
      useAuthStore.getState().clearAuth();

      await expect(apiClient.get('/test')).rejects.toThrow(
        'Authentication required'
      );

      expect(window.location.href).toBe('/login');
    });

    it('should not require token when requiresAuth is false', async () => {
      useAuthStore.getState().clearAuth();

      const mockData = { message: 'success' };
      global.fetch = mockFetchSuccess(mockData);

      await apiClient.get('/test', { requiresAuth: false });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.any(String),
          }),
        })
      );
    });

    it('should redirect to login when token is expired', async () => {
      // Set expired token
      const expiresAt = Date.now() - 1000;
      useAuthStore.setState({
        isAuthenticated: true,
        token: mockToken,
        user: mockUser,
        expiresAt,
      });

      await expect(apiClient.get('/test')).rejects.toThrow('Token expired');

      expect(window.location.href).toBe('/login');
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });

  describe('Handle 401 responses', () => {
    it('should clear auth and redirect on 401 response', async () => {
      useAuthStore.getState().setAuth(mockToken, 86400, mockUser);

      global.fetch = mockFetchError(401, 'Unauthorized');

      await expect(apiClient.get('/test')).rejects.toThrow('Unauthorized');

      expect(window.location.href).toBe('/login');
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().token).toBe(null);
    });

    it('should handle 401 without token (already logged out)', async () => {
      useAuthStore.getState().clearAuth();
      global.fetch = mockFetchSuccess({ message: 'success' });

      // Should redirect immediately when no token
      await expect(apiClient.get('/test')).rejects.toThrow(
        'Authentication required'
      );

      expect(window.location.href).toBe('/login');
    });
  });

  describe('Request/response type safety', () => {
    it('should return typed response from GET request', async () => {
      useAuthStore.getState().setAuth(mockToken, 86400, mockUser);

      interface TestResponse {
        id: number;
        name: string;
      }

      const mockData: TestResponse = { id: 1, name: 'test' };
      global.fetch = mockFetchSuccess(mockData);

      const response = await apiClient.get<TestResponse>('/test');

      expect(response).toEqual(mockData);
      expect(response.id).toBe(1);
      expect(response.name).toBe('test');
    });

    it('should return typed response from POST request', async () => {
      useAuthStore.getState().setAuth(mockToken, 86400, mockUser);

      interface CreateResponse {
        success: boolean;
        id: number;
      }

      const mockData: CreateResponse = { success: true, id: 123 };
      global.fetch = mockFetchSuccess(mockData);

      const response = await apiClient.post<CreateResponse>('/test', {
        name: 'new item',
      });

      expect(response).toEqual(mockData);
      expect(response.success).toBe(true);
      expect(response.id).toBe(123);
    });
  });

  describe('HTTP methods', () => {
    beforeEach(() => {
      useAuthStore.getState().setAuth(mockToken, 86400, mockUser);
    });

    it('should make GET request with correct method', async () => {
      global.fetch = mockFetchSuccess({ data: 'test' });

      await apiClient.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('should make POST request with data', async () => {
      global.fetch = mockFetchSuccess({ success: true });

      const postData = { name: 'test' };
      await apiClient.post('/test', postData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
        })
      );
    });

    it('should make PUT request with data', async () => {
      global.fetch = mockFetchSuccess({ success: true });

      const putData = { id: 1, name: 'updated' };
      await apiClient.put('/test', putData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData),
        })
      );
    });

    it('should make DELETE request', async () => {
      global.fetch = mockFetchSuccess({ success: true });

      await apiClient.del('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('Error handling', () => {
    beforeEach(() => {
      useAuthStore.getState().setAuth(mockToken, 86400, mockUser);
    });

    it('should throw ApiError for HTTP errors', async () => {
      global.fetch = mockFetchError(500, 'Internal Server Error');

      await expect(apiClient.get('/test')).rejects.toThrow();

      try {
        await apiClient.get('/test');
      } catch (error) {
        expect(error).toBeInstanceOf(apiClient.ApiError);
        if (error instanceof apiClient.ApiError) {
          expect(error.status).toBe(500);
          expect(error.statusText).toBe('Internal Server Error');
        }
      }
    });

    it('should extract error message from response body', async () => {
      const errorMessage = 'Custom error message';
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 400,
          statusText: 'Bad Request',
          json: () => Promise.resolve({ detail: errorMessage }),
        } as Response)
      );

      await expect(apiClient.get('/test')).rejects.toThrow(errorMessage);
    });

    it('should handle network errors', async () => {
      global.fetch = mockFetchNetworkError();

      await expect(apiClient.get('/test')).rejects.toThrow(
        'Network error. Please check your connection.'
      );
    });

    it('should handle 404 errors', async () => {
      global.fetch = mockFetchError(404, 'Not Found');

      await expect(apiClient.get('/test')).rejects.toThrow();

      try {
        await apiClient.get('/test');
      } catch (error) {
        if (error instanceof apiClient.ApiError) {
          expect(error.status).toBe(404);
        }
      }
    });
  });

  describe('Request headers', () => {
    beforeEach(() => {
      useAuthStore.getState().setAuth(mockToken, 86400, mockUser);
    });

    it('should include Content-Type header', async () => {
      global.fetch = mockFetchSuccess({ data: 'test' });

      await apiClient.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should merge custom headers', async () => {
      global.fetch = mockFetchSuccess({ data: 'test' });

      await apiClient.get('/test', {
        headers: {
          'X-Custom-Header': 'custom-value',
        },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            Authorization: `Bearer ${mockToken}`,
            'X-Custom-Header': 'custom-value',
          }),
        })
      );
    });
  });

  describe('URL construction', () => {
    beforeEach(() => {
      useAuthStore.getState().setAuth(mockToken, 86400, mockUser);
    });

    it('should construct correct URL with base path', async () => {
      global.fetch = mockFetchSuccess({ data: 'test' });

      await apiClient.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/test'),
        expect.any(Object)
      );
    });

    it('should handle endpoints without leading slash', async () => {
      global.fetch = mockFetchSuccess({ data: 'test' });

      await apiClient.get('test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1test'),
        expect.any(Object)
      );
    });
  });
});
