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
  const formData = new FormData();
  formData.append('file', file);
  formData.append('model_id', modelId);

  // Use uploadFile with multipart/form-data
  const endpoint = `/restore?model_id=${encodeURIComponent(modelId)}`;

  return uploadFile<RestoreResponse>(endpoint, file, onProgress);
}
