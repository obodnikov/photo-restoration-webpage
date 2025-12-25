/**
 * Model configuration service
 * Handles API calls for model configuration management
 */
import * as api from '../../../services/apiClient';
import type {
  ModelConfigListItem,
  ModelConfigDetail,
  ModelConfigCreate,
  ModelConfigUpdate,
  AvailableTagsResponse,
  ModelConfigValidationResponse,
} from '../types';

/**
 * List all model configurations
 */
export async function listModelConfigs(): Promise<ModelConfigListItem[]> {
  const response = await api.get<ModelConfigListItem[]>('/admin/models/config');
  return response;
}

/**
 * Get specific model configuration
 */
export async function getModelConfig(modelId: string): Promise<ModelConfigDetail> {
  const response = await api.get<ModelConfigDetail>(`/admin/models/config/${modelId}`);
  return response;
}

/**
 * Create new model configuration
 */
export async function createModelConfig(config: ModelConfigCreate): Promise<ModelConfigDetail> {
  const response = await api.post<ModelConfigDetail>('/admin/models/config', config);
  return response;
}

/**
 * Update existing model configuration
 */
export async function updateModelConfig(
  modelId: string,
  config: ModelConfigUpdate
): Promise<ModelConfigDetail> {
  const response = await api.put<ModelConfigDetail>(`/admin/models/config/${modelId}`, config);
  return response;
}

/**
 * Delete model configuration from local.json
 */
export async function deleteModelConfig(modelId: string): Promise<void> {
  await api.del(`/admin/models/config/${modelId}`);
}

/**
 * Get available tags and categories
 */
export async function getAvailableTags(): Promise<AvailableTagsResponse> {
  const response = await api.get<AvailableTagsResponse>('/admin/models/tags');
  return response;
}

/**
 * Validate model configuration
 */
export async function validateModelConfig(
  config: Record<string, any>
): Promise<ModelConfigValidationResponse> {
  const response = await api.post<ModelConfigValidationResponse>('/admin/models/validate', config);
  return response;
}

/**
 * Reload model configurations
 */
export async function reloadModelConfigs(): Promise<{ success: boolean; message: string }> {
  const response = await api.post<{ success: boolean; message: string }>('/admin/models/reload', {});
  return response;
}
