/**
 * Tests for ModelSelector component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { ModelSelector } from '../ModelSelector';
import * as restorationService from '../../services/restorationService';
import type { ModelInfo, ModelParameterValues } from '../../types';

vi.mock('../../services/restorationService');

describe('ModelSelector', () => {
  const mockModels: ModelInfo[] = [
    {
      id: 'model-1',
      name: 'Model One',
      model: 'test/model-1',
      category: 'restore',
      description: 'First test model',
      tags: ['tag1', 'tag2'],
    },
    {
      id: 'model-2',
      name: 'Model Two',
      model: 'test/model-2',
      category: 'enhance',
      description: 'Second test model',
      tags: ['tag3'],
    },
  ];

  const mockOnSelectModel = vi.fn();
  const mockOnParameterChange = vi.fn();
  const mockParameterValues: ModelParameterValues = {};

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show loading state initially', () => {
    vi.mocked(restorationService.fetchModels).mockReturnValue(
      new Promise(() => {}) // Never resolves
    );

    render(
      <ModelSelector
        selectedModel={null}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    expect(screen.getByText('Loading models...')).toBeInTheDocument();
  });

  it('should render models after loading', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue({
      models: mockModels,
      total: 2,
    });

    render(
      <ModelSelector
        selectedModel={null}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Model One')).toBeInTheDocument();
      expect(screen.getByText('Model Two')).toBeInTheDocument();
    });
  });

  it('should auto-select first model if none selected', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue({
      models: mockModels,
      total: 2,
    });

    render(
      <ModelSelector
        selectedModel={null}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      expect(mockOnSelectModel).toHaveBeenCalledWith(mockModels[0]);
    });
  });

  it('should not auto-select if model already selected', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue({
      models: mockModels,
      total: 2,
    });

    render(
      <ModelSelector
        selectedModel={mockModels[1]}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Model One')).toBeInTheDocument();
    });

    expect(mockOnSelectModel).not.toHaveBeenCalled();
  });

  it('should call onSelectModel when model card clicked', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue({
      models: mockModels,
      total: 2,
    });

    render(
      <ModelSelector
        selectedModel={mockModels[0]}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Model Two')).toBeInTheDocument();
    });

    const modelTwoButton = screen.getByText('Model Two').closest('button');
    fireEvent.click(modelTwoButton!);

    expect(mockOnSelectModel).toHaveBeenCalledWith(mockModels[1]);
  });

  it('should show selected model with selected class', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue({
      models: mockModels,
      total: 2,
    });

    render(
      <ModelSelector
        selectedModel={mockModels[0]}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      const selectedButton = screen.getByText('Model One').closest('button');
      expect(selectedButton).toHaveClass('selected');
    });
  });

  it('should display model tags', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue({
      models: mockModels,
      total: 2,
    });

    render(
      <ModelSelector
        selectedModel={null}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('tag1')).toBeInTheDocument();
      expect(screen.getByText('tag2')).toBeInTheDocument();
      expect(screen.getByText('tag3')).toBeInTheDocument();
    });
  });

  it('should show error message on load failure', async () => {
    vi.mocked(restorationService.fetchModels).mockRejectedValue(
      new Error('Network error')
    );

    render(
      <ModelSelector
        selectedModel={null}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByText('Failed to load models. Please try again.')
      ).toBeInTheDocument();
    });
  });

  it('should retry loading on error close', async () => {
    vi.mocked(restorationService.fetchModels)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ models: mockModels, total: 2 });

    render(
      <ModelSelector
        selectedModel={null}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByText('Failed to load models. Please try again.')
      ).toBeInTheDocument();
    });

    // Click retry (close button on error)
    const errorMessage = screen.getByText(
      'Failed to load models. Please try again.'
    );
    const closeButton = errorMessage.parentElement?.querySelector('button');
    if (closeButton) {
      fireEvent.click(closeButton);
    }

    await waitFor(() => {
      expect(screen.getByText('Model One')).toBeInTheDocument();
    });
  });

  it('should show empty state when no models available', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue({
      models: [],
      total: 0,
    });

    render(
      <ModelSelector
        selectedModel={null}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No models available')).toBeInTheDocument();
    });
  });

  it('should disable model cards when disabled prop is true', async () => {
    vi.mocked(restorationService.fetchModels).mockResolvedValue({
      models: mockModels,
      total: 2,
    });

    render(
      <ModelSelector
        selectedModel={mockModels[0]}
        onSelectModel={mockOnSelectModel}
        parameterValues={mockParameterValues}
        onParameterChange={mockOnParameterChange}
        disabled={true}
      />
    );

    await waitFor(() => {
      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        if (button.className.includes('model-card')) {
          expect(button).toBeDisabled();
        }
      });
    });
  });

  it('should render ModelParameterControls for selected model', async () => {
    const modelWithParams: ModelInfo = {
      ...mockModels[0],
      schema: {
        parameters: [
          {
            name: 'quality',
            type: 'integer',
            required: false,
            description: 'Quality',
            default: 80,
            min: 1,
            max: 100,
            ui_hidden: false,
          },
        ],
      },
    };

    vi.mocked(restorationService.fetchModels).mockResolvedValue({
      models: [modelWithParams],
      total: 1,
    });

    render(
      <ModelSelector
        selectedModel={modelWithParams}
        onSelectModel={mockOnSelectModel}
        parameterValues={{ quality: 80 }}
        onParameterChange={mockOnParameterChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Parameters')).toBeInTheDocument();
      expect(screen.getByText('Quality')).toBeInTheDocument();
    });
  });
});
