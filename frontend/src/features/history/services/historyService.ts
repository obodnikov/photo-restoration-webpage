/**
 * History service for API calls
 * Handles fetching, viewing, and deleting history items
 */

import { get, del } from '../../../services/apiClient';
import type { HistoryResponse, ImageDetailResponse, DeleteResponse } from '../types';

/**
 * Fetch history with pagination
 */
export async function fetchHistory(
  limit: number = 20,
  offset: number = 0
): Promise<HistoryResponse> {
  return get<HistoryResponse>(`/restore/history?limit=${limit}&offset=${offset}`);
}

/**
 * Get specific image details
 */
export async function getImageDetail(imageId: string): Promise<ImageDetailResponse> {
  return get<ImageDetailResponse>(`/restore/${imageId}`);
}

/**
 * Delete processed image
 */
export async function deleteImage(imageId: string): Promise<DeleteResponse> {
  return del<DeleteResponse>(`/restore/${imageId}`);
}

/**
 * Get download URL for processed image
 */
export function getDownloadUrl(imageId: string): string {
  return `/restore/${imageId}/download`;
}
