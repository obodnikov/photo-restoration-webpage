/**
 * Frontend configuration from environment variables.
 */

export const config = {
  // API base URL - use relative path for reverse proxy compatibility
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api/v1',

  // App settings
  appName: import.meta.env.VITE_APP_NAME || 'Photo Restoration',
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',

  // File upload
  maxFileSize: 10 * 1024 * 1024, // 10MB
  allowedFileTypes: ['image/jpeg', 'image/jpg', 'image/png'],
  allowedExtensions: ['.jpg', '.jpeg', '.png'],
} as const;
