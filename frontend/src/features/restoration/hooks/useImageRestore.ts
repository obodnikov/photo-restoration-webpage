/**
 * useImageRestore hook
 * Manages image restoration state and logic
 */

import { useState } from 'react';
import { restoreImage } from '../services/restorationService';
import type { ModelInfo, RestoreResponse, ImageViewMode } from '../types';
import { config } from '../../../config/config';

export interface UseImageRestoreResult {
  selectedModel: ModelInfo | null;
  selectedFile: File | null;
  originalImageUrl: string | null;
  processedImageUrl: string | null;
  viewMode: ImageViewMode;
  isProcessing: boolean;
  progress: number;
  error: string | null;
  result: RestoreResponse | null;
  setSelectedModel: (model: ModelInfo | null) => void;
  setSelectedFile: (file: File | null) => void;
  setViewMode: (mode: ImageViewMode) => void;
  uploadAndRestore: () => Promise<void>;
  reset: () => void;
  downloadProcessed: () => void;
}

export function useImageRestore(): UseImageRestoreResult {
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [originalImageUrl, setOriginalImageUrl] = useState<string | null>(null);
  const [processedImageUrl, setProcessedImageUrl] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ImageViewMode>('both');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RestoreResponse | null>(null);

  const uploadAndRestore = async () => {
    if (!selectedFile || !selectedModel) {
      setError('Please select a file and model');
      return;
    }

    try {
      setIsProcessing(true);
      setError(null);
      setProgress(0);

      // Upload and process
      const response = await restoreImage(
        selectedFile,
        selectedModel.id,
        (uploadProgress) => {
          setProgress(uploadProgress);
        }
      );

      // Set result URLs
      const baseUrl = config.apiBaseUrl.replace('/api/v1', '');
      setOriginalImageUrl(`${baseUrl}${response.original_url}`);
      setProcessedImageUrl(`${baseUrl}${response.processed_url}`);
      setResult(response);
      setProgress(100);
    } catch (err: any) {
      console.error('Restoration error:', err);
      console.error('Error details:', {
        status: err.status,
        statusText: err.statusText,
        message: err.message,
        fullError: JSON.stringify(err, null, 2)
      });

      // Map backend errors to user-friendly messages
      let errorMessage = 'Failed to process image. Please try again.';

      if (err.status === 400) {
        errorMessage = err.message || 'Invalid image file or parameters.';
      } else if (err.status === 413) {
        errorMessage = 'Image file is too large. Maximum size is 10MB.';
      } else if (err.status === 422) {
        // Unprocessable Entity - validation error
        errorMessage = err.message || 'Invalid request. Please check the file and model selection.';
      } else if (err.status === 503) {
        errorMessage = 'AI service is temporarily unavailable. Please try again later.';
      } else if (err.status === 504) {
        errorMessage = 'Request timeout. The image might be too complex. Try a smaller image.';
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const reset = () => {
    setSelectedFile(null);
    setOriginalImageUrl(null);
    setProcessedImageUrl(null);
    setViewMode('both');
    setIsProcessing(false);
    setProgress(0);
    setError(null);
    setResult(null);
  };

  const downloadProcessed = () => {
    if (!processedImageUrl) return;

    const link = document.createElement('a');
    link.href = processedImageUrl;
    link.download = `restored-${selectedFile?.name || 'image.jpg'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return {
    selectedModel,
    selectedFile,
    originalImageUrl,
    processedImageUrl,
    viewMode,
    isProcessing,
    progress,
    error,
    result,
    setSelectedModel,
    setSelectedFile,
    setViewMode,
    uploadAndRestore,
    reset,
    downloadProcessed,
  };
}
