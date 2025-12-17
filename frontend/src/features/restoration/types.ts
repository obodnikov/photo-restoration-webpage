/**
 * Type definitions for the restoration feature
 */

/**
 * Model information from API
 */
export interface ModelInfo {
  id: string;
  name: string;
  model: string;
  category: string;
  description: string;
  parameters?: Record<string, unknown>;
  tags?: string[];
  version?: string;
}

/**
 * Model list response
 */
export interface ModelListResponse {
  models: ModelInfo[];
  total: number;
}

/**
 * Restoration response from API
 */
export interface RestoreResponse {
  id: string;
  original_url: string;
  processed_url: string;
  model_id: string;
  timestamp: string;
  session_id: string;
}

/**
 * Image view mode for comparison
 */
export type ImageViewMode = 'original' | 'processed' | 'both';

/**
 * Upload progress callback
 */
export type UploadProgressCallback = (progress: number) => void;

/**
 * Restoration state
 */
export interface RestorationState {
  selectedModel: ModelInfo | null;
  selectedFile: File | null;
  originalImageUrl: string | null;
  processedImageUrl: string | null;
  viewMode: ImageViewMode;
  isProcessing: boolean;
  progress: number;
  error: string | null;
  result: RestoreResponse | null;
}
