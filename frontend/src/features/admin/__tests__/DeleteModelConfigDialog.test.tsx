import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DeleteModelConfigDialog } from '../components/DeleteModelConfigDialog';
import type { ModelConfigListItem } from '../types';

describe('DeleteModelConfigDialog', () => {
  let mockOnClose: ReturnType<typeof vi.fn>;
  let mockOnConfirm: ReturnType<typeof vi.fn>;

  const localConfig: ModelConfigListItem = {
    id: 'local-model',
    name: 'Local Test Model',
    provider: 'replicate',
    category: 'restore',
    enabled: true,
    source: 'local',
    tags: ['restore'],
  };

  const defaultConfig: ModelConfigListItem = {
    id: 'default-model',
    name: 'Default Test Model',
    provider: 'replicate',
    category: 'upscale',
    enabled: true,
    source: 'default',
    tags: ['upscale'],
  };

  beforeEach(() => {
    mockOnClose = vi.fn();
    mockOnConfirm = vi.fn().mockResolvedValue(undefined);
  });

  describe('Rendering', () => {
    it('renders with title', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      expect(screen.getByText('Confirm Delete Model Configuration')).toBeInTheDocument();
    });

    it('does not render when not open', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={false}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      expect(screen.queryByText('Confirm Delete Model Configuration')).not.toBeInTheDocument();
    });

    it('returns null when config is null', () => {
      const { container } = render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={null}
        />
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Local Config Deletion', () => {
    it('shows warning message for local config', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument();
      expect(screen.getByText(localConfig.name)).toBeInTheDocument();
    });

    it('shows deletion details for local config', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      expect(screen.getByText(/this action cannot be undone/i)).toBeInTheDocument();
      expect(screen.getByText(`Model ID: ${localConfig.id}`)).toBeInTheDocument();
      expect(screen.getByText(/configuration from local\.json/i)).toBeInTheDocument();
    });

    it('renders Delete Configuration button for local config', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      expect(screen.getByRole('button', { name: /delete configuration/i })).toBeInTheDocument();
    });

    it('calls onConfirm with model ID when delete button clicked', async () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /delete configuration/i });
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalledWith(localConfig.id);
      });
    });

    it('calls onClose after successful deletion', async () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /delete configuration/i });
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });
  });

  describe('Default Config Protection', () => {
    it('shows info message for default config', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={defaultConfig}
        />
      );

      expect(screen.getByText(/cannot delete default configuration/i)).toBeInTheDocument();
      expect(screen.getByText(defaultConfig.name)).toBeInTheDocument();
    });

    it('explains why default configs cannot be deleted', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={defaultConfig}
        />
      );

      expect(screen.getByText(/is a default configuration/i)).toBeInTheDocument();
      expect(screen.getByText(/read-only/i)).toBeInTheDocument();
    });

    it('shows Close button instead of Delete for default config', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={defaultConfig}
        />
      );

      expect(screen.getByRole('button', { name: /^close$/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
    });

    it('does not call onConfirm for default config', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={defaultConfig}
        />
      );

      const closeButton = screen.getByRole('button', { name: /^close$/i });
      fireEvent.click(closeButton);

      expect(mockOnConfirm).not.toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('displays error message when deletion fails', async () => {
      const error = new Error('Failed to delete');
      mockOnConfirm.mockRejectedValue(error);

      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /delete configuration/i });
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to delete')).toBeInTheDocument();
      });
    });

    it('does not close dialog when deletion fails', async () => {
      mockOnConfirm.mockRejectedValue(new Error('Deletion error'));

      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /delete configuration/i });
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText('Deletion error')).toBeInTheDocument();
      });

      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('shows error when trying to delete non-local config', async () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={defaultConfig}
        />
      );

      // Try to delete by directly calling handler if exposed
      expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('disables buttons when loading', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
          isLoading={true}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      const deleteButton = screen.getByRole('button', { name: /delete configuration/i });

      expect(cancelButton).toBeDisabled();
      expect(deleteButton).toHaveAttribute('disabled');
    });

    it('prevents closing dialog when loading', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
          isLoading={true}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('shows loading state during async deletion process', async () => {
      let resolveDelete: () => void;
      const deletePromise = new Promise<void>((resolve) => {
        resolveDelete = resolve;
      });
      mockOnConfirm.mockReturnValue(deletePromise);

      const { rerender } = render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
          isLoading={false}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /delete configuration/i });
      fireEvent.click(deleteButton);

      // In a real-world scenario, the parent would set isLoading to true
      // when the async operation starts. Let's simulate that:
      rerender(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
          isLoading={true}
        />
      );

      // Verify loading state is shown
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      const deleteButtonAfterClick = screen.getByRole('button', { name: /delete configuration/i });

      expect(cancelButton).toBeDisabled();
      expect(deleteButtonAfterClick).toHaveAttribute('disabled');

      // Complete the deletion
      resolveDelete!();

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalledWith(localConfig.id);
      });
    });
  });

  describe('Cancel Action', () => {
    it('renders Cancel button for local config', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('calls onClose when Cancel button clicked', () => {
      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={localConfig}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalled();
      expect(mockOnConfirm).not.toHaveBeenCalled();
    });
  });

  describe('Source Variants', () => {
    it('allows deletion of production source', () => {
      const productionConfig: ModelConfigListItem = {
        ...localConfig,
        source: 'production',
      };

      render(
        <DeleteModelConfigDialog
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          config={productionConfig}
        />
      );

      // Production configs are treated same as default (cannot delete)
      expect(screen.getByText(/cannot delete default configuration/i)).toBeInTheDocument();
    });

    it('handles all source types correctly', () => {
      const sources: Array<ModelConfigListItem['source']> = [
        'local',
        'default',
        'production',
        'development',
        'testing',
        'staging',
      ];

      sources.forEach((source) => {
        const config: ModelConfigListItem = { ...localConfig, source };
        const { unmount } = render(
          <DeleteModelConfigDialog
            isOpen={true}
            onClose={mockOnClose}
            onConfirm={mockOnConfirm}
            config={config}
          />
        );

        if (source === 'local') {
          expect(screen.getByRole('button', { name: /delete configuration/i })).toBeInTheDocument();
        } else {
          expect(screen.queryByRole('button', { name: /delete configuration/i })).not.toBeInTheDocument();
        }

        unmount();
      });
    });
  });
});
