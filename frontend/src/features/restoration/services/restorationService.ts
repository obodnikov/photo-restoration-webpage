/**
 * Restoration service for API calls
 * Handles model fetching and image restoration
 */

import { get } from '../../../services/apiClient';
import { uploadFile } from '../../../services/apiClient';
import type { ModelListResponse, RestoreResponse, UploadProgressCallback } from '../types';

/**
 * Fetch available models from API
 */
export async function fetchModels(): Promise<ModelListResponse> {
  return get<ModelListResponse>('/models');
}

/**
 * Upload and restore an image
 */
export async function restoreImage(
  file: File,
  modelId: string,
  onProgress?: UploadProgressCallback
): Promise<RestoreResponse> {
  // Backend expects:
  // - file: UploadFile (multipart/form-data)
  // - model_id: Form field (multipart/form-data)
  // So we need to send everything as FormData, not in query params
  const endpoint = `/restore`;

  // uploadFile handles creating FormData with the file
  // but we need to also send model_id as a form field
  return uploadFile<RestoreResponse>(endpoint, file, onProgress, { modelId });
}
