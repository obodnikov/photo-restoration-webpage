import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { JsonPreview } from '../components/JsonPreview';

// Mock clipboard API
const mockWriteText = vi.fn();
Object.assign(navigator, {
  clipboard: {
    writeText: mockWriteText,
  },
});

describe('JsonPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders with Live Preview title', () => {
      render(<JsonPreview data={{}} />);

      expect(screen.getByText('Live Preview')).toBeInTheDocument();
    });

    it('displays valid status for valid JSON data', () => {
      render(<JsonPreview data={{ key: 'value' }} />);

      expect(screen.getByText('✓')).toBeInTheDocument();
      expect(screen.getByText('Valid JSON')).toBeInTheDocument();
    });

    it('displays formatted JSON in preview', () => {
      const data = { name: 'Test', enabled: true, tags: ['tag1', 'tag2'] };
      render(<JsonPreview data={data} />);

      const preview = screen.getByText(/"name": "Test"/);
      expect(preview).toBeInTheDocument();
    });
  });

  describe('JSON Formatting', () => {
    it('formats JSON with proper indentation', () => {
      const data = {
        id: 'test',
        nested: {
          key: 'value',
        },
      };

      render(<JsonPreview data={data} />);

      const expectedJson = JSON.stringify(data, null, 2);
      const preElement = screen.getByText((content, element) => {
        return element?.tagName.toLowerCase() === 'pre' && element.textContent === expectedJson;
      });
      expect(preElement).toBeInTheDocument();
    });

    it('handles empty object', () => {
      render(<JsonPreview data={{}} />);

      expect(screen.getByText('{}')).toBeInTheDocument();
      expect(screen.getByText('Valid JSON')).toBeInTheDocument();
    });

    it('handles nested arrays', () => {
      const data = {
        items: [1, 2, 3],
        nested: [{ a: 1 }, { b: 2 }],
      };

      render(<JsonPreview data={data} />);

      expect(screen.getByText('Valid JSON')).toBeInTheDocument();
    });
  });

  describe('Copy Functionality', () => {
    it('renders copy button for valid JSON', () => {
      render(<JsonPreview data={{ test: 'value' }} />);

      expect(screen.getByRole('button', { name: /copy/i })).toBeInTheDocument();
    });

    it('copies JSON to clipboard when copy button clicked', async () => {
      mockWriteText.mockResolvedValue(undefined);

      const data = { test: 'value', number: 123 };
      render(<JsonPreview data={data} />);

      const copyButton = screen.getByRole('button', { name: /copy/i });
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalledWith(JSON.stringify(data, null, 2));
      });
    });

    it('shows "Copied!" text temporarily after copying', async () => {
      mockWriteText.mockResolvedValue(undefined);

      render(<JsonPreview data={{ test: 'value' }} />);

      const copyButton = screen.getByRole('button', { name: /copy/i });
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(screen.getByText('Copied!')).toBeInTheDocument();
      });

      // Wait for timeout to reset
      await waitFor(
        () => {
          expect(screen.getByText('Copy')).toBeInTheDocument();
        },
        { timeout: 2500 }
      );
    });

    it('handles clipboard copy errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockWriteText.mockRejectedValue(new Error('Clipboard error'));

      render(<JsonPreview data={{ test: 'value' }} />);

      const copyButton = screen.getByRole('button', { name: /copy/i });
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalled();
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Invalid JSON Handling', () => {
    it('shows invalid status when JSON stringification fails', () => {
      // Create circular reference to cause stringify to fail
      const circular: any = { a: 1 };
      circular.self = circular;

      render(<JsonPreview data={circular} />);

      expect(screen.getByText('✗')).toBeInTheDocument();
      expect(screen.getByText('Invalid JSON')).toBeInTheDocument();
    });

    it('does not show copy button for invalid JSON', () => {
      const circular: any = { a: 1 };
      circular.self = circular;

      render(<JsonPreview data={circular} />);

      expect(screen.queryByRole('button', { name: /copy/i })).not.toBeInTheDocument();
    });

    it('displays error message for invalid JSON', () => {
      const circular: any = { a: 1 };
      circular.self = circular;

      render(<JsonPreview data={circular} />);

      expect(screen.getByText(/circular/i)).toBeInTheDocument();
    });
  });

  describe('Complex Data Types', () => {
    it('handles null values', () => {
      render(<JsonPreview data={{ value: null }} />);

      expect(screen.getByText('Valid JSON')).toBeInTheDocument();
      expect(screen.getByText(/"value": null/)).toBeInTheDocument();
    });

    it('handles boolean values', () => {
      render(<JsonPreview data={{ enabled: true, disabled: false }} />);

      expect(screen.getByText(/"enabled": true/)).toBeInTheDocument();
      expect(screen.getByText(/"disabled": false/)).toBeInTheDocument();
    });

    it('handles number values', () => {
      render(<JsonPreview data={{ count: 42, price: 19.99 }} />);

      expect(screen.getByText(/"count": 42/)).toBeInTheDocument();
      expect(screen.getByText(/"price": 19.99/)).toBeInTheDocument();
    });

    it('handles mixed nested structures', () => {
      const data = {
        string: 'text',
        number: 123,
        boolean: true,
        null: null,
        array: [1, 2, 3],
        object: { nested: 'value' },
      };

      render(<JsonPreview data={data} />);

      expect(screen.getByText('Valid JSON')).toBeInTheDocument();
    });
  });

  describe('Visual States', () => {
    it('applies valid class to status element', () => {
      render(<JsonPreview data={{ test: 'value' }} />);

      const status = screen.getByText('Valid JSON').parentElement;
      expect(status).toHaveClass('json-preview-status', 'valid');
    });

    it('applies invalid class to status element for invalid data', () => {
      const circular: any = {};
      circular.self = circular;

      render(<JsonPreview data={circular} />);

      const status = screen.getByText('Invalid JSON').parentElement;
      expect(status).toHaveClass('json-preview-status', 'invalid');
    });
  });
});
