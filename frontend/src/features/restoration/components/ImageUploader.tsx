/**
 * ImageUploader component with drag & drop support
 * Handles file validation and preview
 */

import React, { useRef, useState } from 'react';

export interface ImageUploaderProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  disabled?: boolean;
  maxSizeMB?: number;
  acceptedFormats?: string[];
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onFileSelect,
  selectedFile,
  disabled = false,
  maxSizeMB = 10,
  acceptedFormats = ['.jpg', '.jpeg', '.png'],
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxSizeBytes) {
      return `File size must be less than ${maxSizeMB}MB`;
    }

    // Check file type
    const extension = `.${file.name.split('.').pop()?.toLowerCase()}`;
    if (!acceptedFormats.includes(extension)) {
      return `Only ${acceptedFormats.join(', ')} files are allowed`;
    }

    // Check if it's actually an image
    if (!file.type.startsWith('image/')) {
      return 'File must be an image';
    }

    return null;
  };

  const handleFileChange = (file: File) => {
    setError(null);

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    onFileSelect(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileChange(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileChange(file);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const handleClear = () => {
    setPreview(null);
    setError(null);
    onFileSelect(null as any);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="image-uploader">
      <div
        className={`uploader-dropzone ${isDragging ? 'dragging' : ''} ${
          disabled ? 'disabled' : ''
        } ${selectedFile ? 'has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFormats.join(',')}
          onChange={handleInputChange}
          disabled={disabled}
          className="uploader-input"
        />

        {!selectedFile && !preview && (
          <div className="uploader-placeholder">
            <div className="uploader-icon">📷</div>
            <p className="uploader-text">
              Drag & drop an image here, or click to select
            </p>
            <p className="uploader-hint">
              Supported formats: {acceptedFormats.join(', ')} (max {maxSizeMB}MB)
            </p>
          </div>
        )}

        {preview && (
          <div className="uploader-preview">
            <img src={preview} alt="Preview" className="preview-image" />
            <div className="preview-overlay">
              <p className="preview-filename">{selectedFile?.name}</p>
              <button
                type="button"
                className="btn btn-secondary btn-small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClear();
                }}
              >
                Change Image
              </button>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="uploader-error">
          <p>{error}</p>
        </div>
      )}

      {selectedFile && !error && (
        <div className="uploader-info">
          <p>
            <strong>Selected:</strong> {selectedFile.name} (
            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
          </p>
        </div>
      )}
    </div>
  );
};
