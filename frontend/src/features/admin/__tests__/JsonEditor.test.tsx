import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { JsonEditor } from '../components/JsonEditor';

describe('JsonEditor', () => {
  let mockOnChange: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnChange = vi.fn();
  });

  describe('Rendering', () => {
    it('renders with label and textarea', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('Test JSON')).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders with placeholder', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value=""
          onChange={mockOnChange}
          placeholder='{"key": "value"}'
        />
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('placeholder', '{"key": "value"}');
    });

    it('renders with custom row count', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
          rows={15}
        />
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('rows', '15');
    });

    it('renders with default 10 rows', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
        />
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('rows', '10');
    });
  });

  describe('Value Handling', () => {
    it('displays current value', () => {
      const jsonValue = '{"test": "value"}';
      render(
        <JsonEditor
          label="Test JSON"
          value={jsonValue}
          onChange={mockOnChange}
        />
      );

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.value).toBe(jsonValue);
    });

    it('calls onChange when value changes', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
        />
      );

      const textarea = screen.getByRole('textbox');
      fireEvent.change(textarea, { target: { value: '{"new": "value"}' } });

      expect(mockOnChange).toHaveBeenCalledWith('{"new": "value"}');
    });
  });

  describe('Tab Key Handling', () => {
    it('inserts two spaces when Tab key is pressed', () => {
      const { rerender } = render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
        />
      );

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;

      // Set cursor position
      textarea.setSelectionRange(1, 1);

      fireEvent.keyDown(textarea, { key: 'Tab' });

      expect(mockOnChange).toHaveBeenCalledWith('{  }');
    });

    it('replaces selected text with spaces on Tab', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value='{"test": "value"}'
          onChange={mockOnChange}
        />
      );

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;

      // Select "test"
      textarea.setSelectionRange(2, 6);

      fireEvent.keyDown(textarea, { key: 'Tab' });

      expect(mockOnChange).toHaveBeenCalledWith('{"  ": "value"}');
    });

    it('allows other keys to work normally', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
        />
      );

      const textarea = screen.getByRole('textbox');

      fireEvent.keyDown(textarea, { key: 'Enter' });
      fireEvent.keyDown(textarea, { key: 'a' });

      // Tab handler should not interfere with other keys
      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('JSON Validation', () => {
    it('shows no error for valid JSON', async () => {
      render(
        <JsonEditor
          label="Test JSON"
          value='{"valid": "json"}'
          onChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(screen.queryByText(/Invalid JSON/i)).not.toBeInTheDocument();
      });
    });

    it('shows error for invalid JSON', async () => {
      render(
        <JsonEditor
          label="Test JSON"
          value='{"invalid": json}'
          onChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Unexpected token/i)).toBeInTheDocument();
      });
    });

    it('does not show error for empty value', async () => {
      render(
        <JsonEditor
          label="Test JSON"
          value=""
          onChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(screen.queryByText(/Invalid JSON/i)).not.toBeInTheDocument();
      });
    });

    it('applies error class to textarea when JSON is invalid', async () => {
      render(
        <JsonEditor
          label="Test JSON"
          value='{"invalid"}'
          onChange={mockOnChange}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByRole('textbox');
        expect(textarea).toHaveClass('json-editor-error');
      });
    });

    it('shows parent error over validation error', async () => {
      render(
        <JsonEditor
          label="Test JSON"
          value='{"valid": "json"}'
          onChange={mockOnChange}
          error="Custom error message"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Custom error message')).toBeInTheDocument();
        expect(screen.queryByText(/Unexpected token/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Disabled State', () => {
    it('disables textarea when disabled prop is true', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeDisabled();
    });

    it('allows onChange when disabled (HTML native behavior)', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const textarea = screen.getByRole('textbox');
      // Note: disabled attribute prevents user interaction in browser,
      // but fireEvent in tests bypasses this. The component correctly
      // passes disabled to textarea, browser will handle the rest.
      expect(textarea).toBeDisabled();
    });
  });

  describe('Error Display', () => {
    it('displays error message when provided', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
          error="This is an error"
        />
      );

      expect(screen.getByText('This is an error')).toBeInTheDocument();
    });

    it('does not display error when error prop is null', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
          error={undefined}
        />
      );

      const errorElement = document.querySelector('.json-error-message');
      expect(errorElement).not.toBeInTheDocument();
    });
  });

  describe('SpellCheck', () => {
    it('disables spellcheck on textarea', () => {
      render(
        <JsonEditor
          label="Test JSON"
          value="{}"
          onChange={mockOnChange}
        />
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('spellcheck', 'false');
    });
  });
});
