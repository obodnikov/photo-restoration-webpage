/**
 * Restoration service for API calls
 * Handles model fetching and image restoration
 */

import { get } from '../../../services/apiClient';
import { uploadFile } from '../../../services/apiClient';
import type { ModelListResponse, RestoreResponse, UploadProgressCallback, ModelParameterValues } from '../types';

/**
 * Fetch available models from API
 */
export async function fetchModels(): Promise<ModelListResponse> {
  return get<ModelListResponse>('/models');
}

/**
 * Upload and restore an image with optional parameters
 */
export async function restoreImage(
  file: File,
  modelId: string,
  parameters?: ModelParameterValues,
  onProgress?: UploadProgressCallback
): Promise<RestoreResponse> {
  // Backend expects:
  // - file: UploadFile (multipart/form-data)
  // - model_id: Form field (multipart/form-data)
  // - parameters: JSON string (optional, multipart/form-data)
  const endpoint = `/restore`;

  // uploadFile handles creating FormData with the file
  // Pass model_id and parameters as form fields
  return uploadFile<RestoreResponse>(endpoint, file, onProgress, { modelId, parameters });
}
