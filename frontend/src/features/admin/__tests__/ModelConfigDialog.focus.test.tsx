/**
 * Focus management test for ModelConfigDialog
 * Ensures input fields don't lose focus when typing
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ModelConfigDialog } from '../components/ModelConfigDialog';
import type { ModelConfigDetail } from '../types';

describe('ModelConfigDialog - Focus Management', () => {
  const mockOnClose = vi.fn();
  const mockOnSave = vi.fn();

  const mockConfig: ModelConfigDetail = {
    id: 'test-model',
    name: 'Test Model',
    model: 'test/model',
    provider: 'replicate',
    category: 'restore',
    description: 'Test description',
    enabled: true,
    version: '1.0',
    tags: ['test'],
    replicate_schema: {},
    custom: {},
    parameters: {},
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should maintain focus when typing in name field', async () => {
    const user = userEvent.setup();

    render(
      <ModelConfigDialog
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
        config={mockConfig}
        availableTags={['test', 'production']}
        availableCategories={['restore', 'upscale']}
      />
    );

    // Find the name input
    const nameInput = screen.getByDisplayValue('Test Model');
    expect(nameInput).toBeInTheDocument();

    // Focus the input
    nameInput.focus();
    expect(document.activeElement).toBe(nameInput);

    // Type in the input
    await user.clear(nameInput);
    await user.type(nameInput, 'New Model Name');

    // Verify focus is maintained
    await waitFor(() => {
      expect(document.activeElement).toBe(nameInput);
    });

    // Verify value was updated
    expect(nameInput).toHaveValue('New Model Name');
  });

  it('should maintain focus when typing in description field', async () => {
    const user = userEvent.setup();

    render(
      <ModelConfigDialog
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
        config={mockConfig}
        availableTags={['test', 'production']}
        availableCategories={['restore', 'upscale']}
      />
    );

    // Find the description textarea
    const descInput = screen.getByDisplayValue('Test description');
    expect(descInput).toBeInTheDocument();

    // Focus the textarea
    descInput.focus();
    expect(document.activeElement).toBe(descInput);

    // Type in the textarea
    await user.clear(descInput);
    await user.type(descInput, 'New description with multiple words');

    // Verify focus is maintained
    await waitFor(() => {
      expect(document.activeElement).toBe(descInput);
    });

    // Verify value was updated
    expect(descInput).toHaveValue('New description with multiple words');
  });

  it('should not reset form when parent re-renders', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <ModelConfigDialog
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
        config={mockConfig}
        availableTags={['test', 'production']}
        availableCategories={['restore', 'upscale']}
      />
    );

    // Find the name input and change it
    const nameInput = screen.getByDisplayValue('Test Model');
    await user.clear(nameInput);
    await user.type(nameInput, 'Modified');

    // Force a re-render with same props
    rerender(
      <ModelConfigDialog
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
        config={mockConfig}
        availableTags={['test', 'production']}
        availableCategories={['restore', 'upscale']}
      />
    );

    // Value should be preserved (not reset to original)
    await waitFor(() => {
      expect(nameInput).toHaveValue('Modified');
    });
  });

  it('should only reset form when dialog opens', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <ModelConfigDialog
        isOpen={false}
        onClose={mockOnClose}
        onSave={mockOnSave}
        config={mockConfig}
        availableTags={['test', 'production']}
        availableCategories={['restore', 'upscale']}
      />
    );

    // Open dialog
    rerender(
      <ModelConfigDialog
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
        config={mockConfig}
        availableTags={['test', 'production']}
        availableCategories={['restore', 'upscale']}
      />
    );

    // Find the name input and change it
    const nameInput = screen.getByDisplayValue('Test Model');
    await user.clear(nameInput);
    await user.type(nameInput, 'Modified');

    expect(nameInput).toHaveValue('Modified');

    // Re-render with same props (dialog still open)
    rerender(
      <ModelConfigDialog
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
        config={mockConfig}
        availableTags={['test', 'production']}
        availableCategories={['restore', 'upscale']}
      />
    );

    // Value should be preserved
    expect(nameInput).toHaveValue('Modified');

    // Close and reopen dialog
    rerender(
      <ModelConfigDialog
        isOpen={false}
        onClose={mockOnClose}
        onSave={mockOnSave}
        config={mockConfig}
        availableTags={['test', 'production']}
        availableCategories={['restore', 'upscale']}
      />
    );

    rerender(
      <ModelConfigDialog
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
        config={mockConfig}
        availableTags={['test', 'production']}
        availableCategories={['restore', 'upscale']}
      />
    );

    // Value should be reset to original when dialog reopens
    const resetNameInput = screen.getByDisplayValue('Test Model');
    expect(resetNameInput).toHaveValue('Test Model');
  });
});
