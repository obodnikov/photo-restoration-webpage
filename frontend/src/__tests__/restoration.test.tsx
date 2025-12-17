/**
 * Tests for restoration feature
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ImageUploader } from '../features/restoration/components/ImageUploader';
import { ModelSelector } from '../features/restoration/components/ModelSelector';
import { ProcessingStatus } from '../features/restoration/components/ProcessingStatus';
import { ImageComparison } from '../features/restoration/components/ImageComparison';
import { RestorationPage } from '../features/restoration/pages/RestorationPage';
import * as restorationService from '../features/restoration/services/restorationService';

// Mock restoration service
vi.mock('../features/restoration/services/restorationService');

const mockModels = {
  models: [
    {
      id: 'swin2sr-2x',
      name: 'Swin2SR 2x Upscale',
      model: 'caidas/swin2SR-classical-sr-x2-64',
      category: 'upscale',
      description: 'Fast 2x upscaling',
      tags: ['upscale', 'fast'],
    },
    {
      id: 'swin2sr-4x',
      name: 'Swin2SR 4x Upscale',
      model: 'caidas/swin2SR-classical-sr-x4-64',
      category: 'upscale',
      description: 'Fast 4x upscaling',
      tags: ['upscale'],
    },
  ],
  total: 2,
};

describe('ImageUploader Component', () => {
  it('renders upload dropzone', () => {
    const onFileSelect = vi.fn();
    render(<ImageUploader onFileSelect={onFileSelect} selectedFile={null} />);
    expect(screen.getByText(/Drag & drop an image here/i)).toBeInTheDocument();
  });

  it('shows file size and format hints', () => {
    const onFileSelect = vi.fn();
    render(<ImageUploader onFileSelect={onFileSelect} selectedFile={null} />);
    expect(screen.getByText(/Supported formats/i)).toBeInTheDocument();
    expect(screen.getByText(/max 10MB/i)).toBeInTheDocument();
  });

  it('accepts file via input', async () => {
    const onFileSelect = vi.fn();
    const { container } = render(<ImageUploader onFileSelect={onFileSelect} selectedFile={null} />);

    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(onFileSelect).toHaveBeenCalledWith(file);
    });
  });

  it('shows error for invalid file type', async () => {
    const onFileSelect = vi.fn();
    const { container } = render(<ImageUploader onFileSelect={onFileSelect} selectedFile={null} />);

    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/Only .jpg, .jpeg, .png files are allowed/i)).toBeInTheDocument();
    });
  });

  it('shows error for file exceeding size limit', async () => {
    const onFileSelect = vi.fn();
    const { container } = render(<ImageUploader onFileSelect={onFileSelect} selectedFile={null} maxSizeMB={1} />);

    // Create a file larger than 1MB
    const largeFile = new File([new ArrayBuffer(2 * 1024 * 1024)], 'large.jpg', { type: 'image/jpeg' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [largeFile] } });

    await waitFor(() => {
      expect(screen.getByText(/File size must be less than/i)).toBeInTheDocument();
    });
  });

  it('disables dropzone when disabled prop is true', () => {
    const onFileSelect = vi.fn();
    const { container } = render(<ImageUploader onFileSelect={onFileSelect} selectedFile={null} disabled />);
    const dropzone = container.querySelector('.uploader-dropzone');
    expect(dropzone).toHaveClass('disabled');
  });
});

describe('ModelSelector Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and displays models', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue(mockModels);

    const onSelectModel = vi.fn();
    render(<ModelSelector selectedModel={null} onSelectModel={onSelectModel} />);

    await waitFor(() => {
      expect(screen.getByText('Swin2SR 2x Upscale')).toBeInTheDocument();
      expect(screen.getByText('Swin2SR 4x Upscale')).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching models', () => {
    vi.mocked(restorationService.fetchModels).mockImplementation(() =>
      new Promise(() => {}) // Never resolves
    );

    const onSelectModel = vi.fn();
    render(<ModelSelector selectedModel={null} onSelectModel={onSelectModel} />);

    expect(screen.getByText('Loading models...')).toBeInTheDocument();
  });

  it('shows error when fetch fails', async () => {
    vi.mocked(restorationService.fetchModels).mockRejectedValue(new Error('Network error'));

    const onSelectModel = vi.fn();
    render(<ModelSelector selectedModel={null} onSelectModel={onSelectModel} />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load models/i)).toBeInTheDocument();
    });
  });

  it('highlights selected model', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue(mockModels);

    const selectedModel = mockModels.models[0];
    const onSelectModel = vi.fn();
    render(<ModelSelector selectedModel={selectedModel} onSelectModel={onSelectModel} />);

    await waitFor(() => {
      const modelCard = screen.getByText('Swin2SR 2x Upscale').closest('.model-card');
      expect(modelCard).toHaveClass('selected');
    });
  });

  it('calls onSelectModel when model is clicked', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue(mockModels);

    const onSelectModel = vi.fn();
    render(<ModelSelector selectedModel={null} onSelectModel={onSelectModel} />);

    await waitFor(() => {
      fireEvent.click(screen.getByText('Swin2SR 2x Upscale'));
    });

    expect(onSelectModel).toHaveBeenCalledWith(mockModels.models[0]);
  });
});

describe('ProcessingStatus Component', () => {
  it('does not render when not processing', () => {
    const { container } = render(<ProcessingStatus isProcessing={false} progress={0} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders when processing', () => {
    render(<ProcessingStatus isProcessing={true} progress={50} />);
    expect(screen.getByText('Processing your image...')).toBeInTheDocument();
  });

  it('displays progress percentage', () => {
    render(<ProcessingStatus isProcessing={true} progress={75} />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('displays custom message', () => {
    render(<ProcessingStatus isProcessing={true} progress={50} message="Custom message" />);
    expect(screen.getByText('Custom message')).toBeInTheDocument();
  });
});

describe('ImageComparison Component', () => {
  const mockUrls = {
    original: '/uploads/original.jpg',
    processed: '/processed/processed.jpg',
  };

  it('renders view mode buttons', () => {
    const onViewModeChange = vi.fn();
    render(
      <ImageComparison
        originalUrl={mockUrls.original}
        processedUrl={mockUrls.processed}
        viewMode="both"
        onViewModeChange={onViewModeChange}
      />
    );

    // Check that view mode buttons exist
    expect(screen.getAllByText('Original').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Restored').length).toBeGreaterThan(0);
    expect(screen.getByText('Compare')).toBeInTheDocument();
  });

  it('highlights active view mode', () => {
    const onViewModeChange = vi.fn();
    render(
      <ImageComparison
        originalUrl={mockUrls.original}
        processedUrl={mockUrls.processed}
        viewMode="original"
        onViewModeChange={onViewModeChange}
      />
    );

    // Get the button from view-mode-buttons div
    const originalButtons = screen.getAllByText('Original');
    const originalButton = originalButtons[0]; // The button is the first element
    expect(originalButton).toHaveClass('active');
  });

  it('changes view mode when button clicked', () => {
    const onViewModeChange = vi.fn();
    render(
      <ImageComparison
        originalUrl={mockUrls.original}
        processedUrl={mockUrls.processed}
        viewMode="both"
        onViewModeChange={onViewModeChange}
      />
    );

    // Use getAllByText and select the button (first element)
    const originalButtons = screen.getAllByText('Original');
    fireEvent.click(originalButtons[0]);
    expect(onViewModeChange).toHaveBeenCalledWith('original');
  });

  it('shows both images in compare mode', () => {
    const onViewModeChange = vi.fn();
    const { container } = render(
      <ImageComparison
        originalUrl={mockUrls.original}
        processedUrl={mockUrls.processed}
        viewMode="both"
        onViewModeChange={onViewModeChange}
      />
    );

    const images = container.querySelectorAll('img');
    expect(images).toHaveLength(2);
  });

  it('calls onDownload when download button clicked', () => {
    const onViewModeChange = vi.fn();
    const onDownload = vi.fn();
    render(
      <ImageComparison
        originalUrl={mockUrls.original}
        processedUrl={mockUrls.processed}
        viewMode="both"
        onViewModeChange={onViewModeChange}
        onDownload={onDownload}
      />
    );

    fireEvent.click(screen.getByText('Download Restored'));
    expect(onDownload).toHaveBeenCalled();
  });
});
