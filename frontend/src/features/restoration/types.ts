/**
 * Type definitions for the restoration feature
 */

/**
 * UI control types for parameter inputs
 */
export type UIControlType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'slider'
  | 'dropdown'
  | 'radio'
  | 'toggle'
  | 'checkbox';

/**
 * UI control configuration for a parameter
 */
export interface UIControlConfig {
  type: UIControlType;
  label?: string;
  help?: string;
  options?: string[];
  order?: number;
  step?: number;
  marks?: Record<string, string>;
}

/**
 * Parameter schema from model configuration
 */
export interface ParameterSchema {
  name: string;
  type: 'string' | 'integer' | 'float' | 'boolean' | 'enum';
  required: boolean;
  description: string;
  default?: any;
  min?: number;
  max?: number;
  values?: string[];
  ui_hidden?: boolean;
  ui_group?: string;
}

/**
 * Model schema containing parameters
 */
export interface ModelSchema {
  parameters: ParameterSchema[];
  custom?: {
    max_file_size_mb: number;
    supported_formats: string[];
    estimated_time_seconds?: number;
  };
}

/**
 * Custom model configuration
 */
export interface ModelCustomConfig {
  ui_controls?: Record<string, UIControlConfig>;
  [key: string]: any; // Allow other custom fields
}

/**
 * Model parameter values (user-configured)
 */
export interface ModelParameterValues {
  [paramName: string]: any;
}

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
  schema?: ModelSchema;
  custom?: ModelCustomConfig;
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
