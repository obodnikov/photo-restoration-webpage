/**
 * API client with automatic authentication token injection.
 *
 * This module provides typed HTTP methods that automatically:
 * - Inject the JWT token from auth store
 * - Handle 401 responses (auto-redirect to login)
 * - Provide user-friendly error messages
 */

import { config } from '../config/config';
import { useAuthStore } from './authStore';

/**
 * API Error class
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Request options interface
 */
interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
}

/**
 * Make an authenticated API request
 */
async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { requiresAuth = true, headers, ...restOptions } = options;

  // Build request headers
  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Merge custom headers if provided
  if (headers) {
    if (headers instanceof Headers) {
      headers.forEach((value, key) => {
        requestHeaders[key] = value;
      });
    } else if (Array.isArray(headers)) {
      headers.forEach(([key, value]) => {
        requestHeaders[key] = value;
      });
    } else {
      Object.entries(headers).forEach(([key, value]) => {
        requestHeaders[key] = value;
      });
    }
  }

  // Add auth token if required
  if (requiresAuth) {
    const token = useAuthStore.getState().token;

    if (!token) {
      // No token available, redirect to login
      window.location.href = '/login';
      throw new Error('Authentication required');
    }

    // Check if token is expired
    if (useAuthStore.getState().isTokenExpired()) {
      console.log('Token expired, redirecting to login...');
      useAuthStore.getState().clearAuth();
      window.location.href = '/login';
      throw new Error('Token expired');
    }

    requestHeaders['Authorization'] = `Bearer ${token}`;
  }

  // Make request
  const url = `${config.apiBaseUrl}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: requestHeaders,
    });

    // Handle 401 Unauthorized
    if (response.status === 401) {
      console.log('Received 401, clearing auth and redirecting to login...');
      useAuthStore.getState().clearAuth();
      window.location.href = '/login';
      throw new ApiError('Unauthorized', 401, response.statusText);
    }

    // Handle other errors
    if (!response.ok) {
      let errorMessage = 'An error occurred';

      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        errorMessage = response.statusText || errorMessage;
      }

      throw new ApiError(errorMessage, response.status, response.statusText);
    }

    // Parse JSON response
    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Network or other errors
    console.error('API request failed:', error);
    throw new Error('Network error. Please check your connection.');
  }
}

/**
 * GET request
 */
export async function get<T>(
  endpoint: string,
  options?: RequestOptions
): Promise<T> {
  return request<T>(endpoint, {
    ...options,
    method: 'GET',
  });
}

/**
 * POST request
 */
export async function post<T>(
  endpoint: string,
  data?: unknown,
  options?: RequestOptions
): Promise<T> {
  return request<T>(endpoint, {
    ...options,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * PUT request
 */
export async function put<T>(
  endpoint: string,
  data?: unknown,
  options?: RequestOptions
): Promise<T> {
  return request<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * DELETE request
 */
export async function del<T>(
  endpoint: string,
  options?: RequestOptions
): Promise<T> {
  return request<T>(endpoint, {
    ...options,
    method: 'DELETE',
  });
}

/**
 * Upload file with progress tracking
 */
export async function uploadFile<T>(
  endpoint: string,
  file: File,
  onProgress?: (progress: number) => void,
  options?: RequestOptions
): Promise<T> {
  const { requiresAuth = true } = options || {};

  const token = useAuthStore.getState().token;

  if (requiresAuth && !token) {
    window.location.href = '/login';
    throw new Error('Authentication required');
  }

  if (requiresAuth && useAuthStore.getState().isTokenExpired()) {
    useAuthStore.getState().clearAuth();
    window.location.href = '/login';
    throw new Error('Token expired');
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const url = `${config.apiBaseUrl}${endpoint}`;

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          onProgress(progress);
        }
      });
    }

    // Handle completion
    xhr.addEventListener('load', () => {
      if (xhr.status === 401) {
        useAuthStore.getState().clearAuth();
        window.location.href = '/login';
        reject(new ApiError('Unauthorized', 401, xhr.statusText));
        return;
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch {
          reject(new Error('Invalid response format'));
        }
      } else {
        let errorMessage = 'Upload failed';
        try {
          const errorData = JSON.parse(xhr.responseText);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          errorMessage = xhr.statusText || errorMessage;
        }
        reject(new ApiError(errorMessage, xhr.status, xhr.statusText));
      }
    });

    // Handle errors
    xhr.addEventListener('error', () => {
      reject(new Error('Network error during upload'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload cancelled'));
    });

    // Prepare and send request
    const formData = new FormData();
    formData.append('file', file);

    xhr.open('POST', url);

    if (requiresAuth && token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    xhr.send(formData);
  });
}
