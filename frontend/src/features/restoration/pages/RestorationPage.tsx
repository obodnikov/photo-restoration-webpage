/**
 * RestorationPage - Main page for image restoration
 */

import React from 'react';
import { ImageUploader } from '../components/ImageUploader';
import { ModelSelector } from '../components/ModelSelector';
import { ProcessingStatus } from '../components/ProcessingStatus';
import { ImageComparison } from '../components/ImageComparison';
import { useImageRestore } from '../hooks/useImageRestore';
import { Button } from '../../../components/Button';
import { ErrorMessage } from '../../../components/ErrorMessage';

export const RestorationPage: React.FC = () => {
  const {
    selectedModel,
    selectedFile,
    originalImageUrl,
    processedImageUrl,
    viewMode,
    isProcessing,
    progress,
    error,
    setSelectedModel,
    setSelectedFile,
    setViewMode,
    uploadAndRestore,
    reset,
    downloadProcessed,
  } = useImageRestore();

  const canRestore = selectedFile && selectedModel && !isProcessing;
  const hasResult = originalImageUrl && processedImageUrl;

  return (
    <div className="restoration-page">
      <div className="container">
        <div className="page-header">
          <h1>AI Photo Restoration</h1>
          <p className="page-subtitle">
            Upload your old or damaged photos and restore them using advanced AI models
          </p>
        </div>

        {error && (
          <ErrorMessage
            message={error}
            title="Restoration Error"
            onClose={() => setSelectedFile(null)}
          />
        )}

        {!hasResult && (
          <>
            <section className="restoration-section">
              <h2>Step 1: Select AI Model</h2>
              <ModelSelector
                selectedModel={selectedModel}
                onSelectModel={setSelectedModel}
                disabled={isProcessing}
              />
            </section>

            <section className="restoration-section">
              <h2>Step 2: Upload Image</h2>
              <ImageUploader
                onFileSelect={setSelectedFile}
                selectedFile={selectedFile}
                disabled={isProcessing}
                maxSizeMB={10}
                acceptedFormats={['.jpg', '.jpeg', '.png']}
              />
            </section>

            <section className="restoration-section">
              <div className="action-buttons">
                <Button
                  variant="gradient"
                  size="large"
                  onClick={uploadAndRestore}
                  disabled={!canRestore}
                  loading={isProcessing}
                >
                  Restore Image
                </Button>
              </div>
            </section>
          </>
        )}

        {isProcessing && (
          <section className="restoration-section">
            <ProcessingStatus
              isProcessing={isProcessing}
              progress={progress}
              message="Processing your image with AI..."
            />
          </section>
        )}

        {hasResult && (
          <>
            <section className="restoration-section">
              <h2>Your Restored Image</h2>
              <ImageComparison
                originalUrl={originalImageUrl}
                processedUrl={processedImageUrl}
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                onDownload={downloadProcessed}
              />
            </section>

            <section className="restoration-section">
              <div className="action-buttons">
                <Button variant="primary" size="large" onClick={reset}>
                  Restore Another Image
                </Button>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
};
