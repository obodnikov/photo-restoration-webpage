/**
 * Type definitions for the history feature
 */

/**
 * History item from API
 */
export interface HistoryItem {
  id: string;
  original_filename: string;
  model_id: string;
  created_at: string;
  original_path: string;
  processed_path: string;
  model_parameters?: Record<string, unknown>;
}

/**
 * History list response with pagination
 */
export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Image detail response
 */
export interface ImageDetailResponse {
  id: string;
  original_filename: string;
  model_id: string;
  created_at: string;
  original_url: string;
  processed_url: string;
  model_parameters?: Record<string, unknown>;
}

/**
 * Delete response
 */
export interface DeleteResponse {
  message: string;
  deleted_id: string;
}
