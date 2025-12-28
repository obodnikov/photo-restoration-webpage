import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TagSelector } from '../components/TagSelector';

describe('TagSelector', () => {
  let mockOnChange: ReturnType<typeof vi.fn>;
  const availableTags = ['restore', 'upscale', 'enhance', 'fast', 'advanced'];

  beforeEach(() => {
    mockOnChange = vi.fn();
  });

  describe('Rendering', () => {
    it('renders with label', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={[]}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('Select Tags')).toBeInTheDocument();
    });

    it('renders all available tags as checkboxes', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={[]}
          onChange={mockOnChange}
        />
      );

      availableTags.forEach((tag) => {
        expect(screen.getByText(tag)).toBeInTheDocument();
        expect(screen.getByLabelText(tag)).toBeInTheDocument();
      });
    });

    it('renders with empty tags array', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={[]}
          selectedTags={[]}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('Select Tags')).toBeInTheDocument();
      expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    });
  });

  describe('Selection State', () => {
    it('checks selected tags', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore', 'fast']}
          onChange={mockOnChange}
        />
      );

      const restoreCheckbox = screen.getByLabelText('restore') as HTMLInputElement;
      const fastCheckbox = screen.getByLabelText('fast') as HTMLInputElement;
      const upscaleCheckbox = screen.getByLabelText('upscale') as HTMLInputElement;

      expect(restoreCheckbox.checked).toBe(true);
      expect(fastCheckbox.checked).toBe(true);
      expect(upscaleCheckbox.checked).toBe(false);
    });

    it('unchecks unselected tags', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore']}
          onChange={mockOnChange}
        />
      );

      availableTags.forEach((tag) => {
        const checkbox = screen.getByLabelText(tag) as HTMLInputElement;
        if (tag === 'restore') {
          expect(checkbox.checked).toBe(true);
        } else {
          expect(checkbox.checked).toBe(false);
        }
      });
    });
  });

  describe('Tag Selection', () => {
    it('calls onChange with added tag when unchecked tag is clicked', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore']}
          onChange={mockOnChange}
        />
      );

      const upscaleCheckbox = screen.getByLabelText('upscale');
      fireEvent.click(upscaleCheckbox);

      expect(mockOnChange).toHaveBeenCalledWith(['restore', 'upscale']);
    });

    it('calls onChange with removed tag when checked tag is clicked', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore', 'upscale', 'fast']}
          onChange={mockOnChange}
        />
      );

      const upscaleCheckbox = screen.getByLabelText('upscale');
      fireEvent.click(upscaleCheckbox);

      expect(mockOnChange).toHaveBeenCalledWith(['restore', 'fast']);
    });

    it('allows selecting first tag from empty selection', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={[]}
          onChange={mockOnChange}
        />
      );

      const restoreCheckbox = screen.getByLabelText('restore');
      fireEvent.click(restoreCheckbox);

      expect(mockOnChange).toHaveBeenCalledWith(['restore']);
    });

    it('allows deselecting last tag to empty array', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore']}
          onChange={mockOnChange}
        />
      );

      const restoreCheckbox = screen.getByLabelText('restore');
      fireEvent.click(restoreCheckbox);

      expect(mockOnChange).toHaveBeenCalledWith([]);
    });
  });

  describe('Multiple Selections', () => {
    it('allows selecting multiple tags', () => {
      const { rerender } = render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={[]}
          onChange={mockOnChange}
        />
      );

      fireEvent.click(screen.getByLabelText('restore'));
      expect(mockOnChange).toHaveBeenLastCalledWith(['restore']);

      // Simulate parent updating selectedTags
      rerender(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore']}
          onChange={mockOnChange}
        />
      );

      fireEvent.click(screen.getByLabelText('fast'));
      expect(mockOnChange).toHaveBeenLastCalledWith(['restore', 'fast']);
    });

    it('maintains order of selected tags', () => {
      const { rerender } = render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore']}
          onChange={mockOnChange}
        />
      );

      fireEvent.click(screen.getByLabelText('upscale'));
      expect(mockOnChange).toHaveBeenCalledWith(['restore', 'upscale']);

      rerender(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore', 'upscale']}
          onChange={mockOnChange}
        />
      );

      fireEvent.click(screen.getByLabelText('fast'));
      expect(mockOnChange).toHaveBeenLastCalledWith(['restore', 'upscale', 'fast']);
    });
  });

  describe('Disabled State', () => {
    it('disables all checkboxes when disabled prop is true', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore']}
          onChange={mockOnChange}
          disabled={true}
        />
      );

      availableTags.forEach((tag) => {
        const checkbox = screen.getByLabelText(tag);
        expect(checkbox).toBeDisabled();
      });
    });

    it('does not call onChange when disabled and checkbox is clicked', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={['restore']}
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const upscaleCheckbox = screen.getByLabelText('upscale');
      fireEvent.click(upscaleCheckbox);

      expect(mockOnChange).not.toHaveBeenCalled();
    });

    it('enables checkboxes when disabled is false', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={[]}
          onChange={mockOnChange}
          disabled={false}
        />
      );

      availableTags.forEach((tag) => {
        const checkbox = screen.getByLabelText(tag);
        expect(checkbox).not.toBeDisabled();
      });
    });
  });

  describe('Label Interaction', () => {
    it('toggles checkbox when label is clicked', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={availableTags}
          selectedTags={[]}
          onChange={mockOnChange}
        />
      );

      const label = screen.getByText('restore');
      fireEvent.click(label);

      expect(mockOnChange).toHaveBeenCalledWith(['restore']);
    });
  });

  describe('Edge Cases', () => {
    it('handles single tag', () => {
      render(
        <TagSelector
          label="Select Tags"
          availableTags={['restore']}
          selectedTags={[]}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByLabelText('restore')).toBeInTheDocument();
      expect(screen.getAllByRole('checkbox')).toHaveLength(1);
    });

    it('handles many tags', () => {
      const manyTags = Array.from({ length: 20 }, (_, i) => `tag${i}`);

      render(
        <TagSelector
          label="Select Tags"
          availableTags={manyTags}
          selectedTags={[]}
          onChange={mockOnChange}
        />
      );

      expect(screen.getAllByRole('checkbox')).toHaveLength(20);
    });

    it('handles tags with spaces and special characters', () => {
      const specialTags = ['super-fast', 'AI Enhanced', 'v2.0'];

      render(
        <TagSelector
          label="Select Tags"
          availableTags={specialTags}
          selectedTags={[]}
          onChange={mockOnChange}
        />
      );

      specialTags.forEach((tag) => {
        expect(screen.getByText(tag)).toBeInTheDocument();
      });
    });
  });
});
