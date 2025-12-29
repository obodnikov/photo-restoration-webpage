/**
 * Tests for ModelParameterControls component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModelParameterControls } from '../ModelParameterControls';
import type { ModelInfo, ModelParameterValues } from '../../types';

describe('ModelParameterControls', () => {
  const mockModel: ModelInfo = {
    id: 'test-model',
    name: 'Test Model',
    model: 'test/model',
    category: 'restore',
    description: 'Test model',
    schema: {
      parameters: [
        {
          name: 'quality',
          type: 'integer',
          required: false,
          description: 'Output quality',
          default: 80,
          min: 1,
          max: 100,
          ui_hidden: false,
        },
        {
          name: 'format',
          type: 'enum',
          required: false,
          description: 'Output format',
          default: 'png',
          values: ['jpg', 'png'],
          ui_hidden: false,
        },
        {
          name: 'seed',
          type: 'integer',
          required: false,
          description: 'Random seed',
          default: 42,
          ui_hidden: true, // Hidden - should not render
        },
      ],
    },
  };

  it('should render parameters section with count', () => {
    const values: ModelParameterValues = { quality: 80, format: 'png' };
    const onChange = vi.fn();

    render(
      <ModelParameterControls
        model={mockModel}
        values={values}
        onChange={onChange}
      />
    );

    expect(screen.getByText('Parameters')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // 2 visible params
  });

  it('should render visible parameters only', () => {
    const values: ModelParameterValues = { quality: 80, format: 'png' };
    const onChange = vi.fn();

    render(
      <ModelParameterControls
        model={mockModel}
        values={values}
        onChange={onChange}
      />
    );

    // Visible parameters
    expect(screen.getByText('Quality')).toBeInTheDocument();
    expect(screen.getByText('Format')).toBeInTheDocument();

    // Hidden parameter should not be rendered
    expect(screen.queryByText('Seed')).not.toBeInTheDocument();
  });

  it('should render custom UI control when specified', () => {
    const modelWithCustom: ModelInfo = {
      ...mockModel,
      custom: {
        ui_controls: {
          quality: {
            type: 'slider',
            label: 'Output Quality',
            marks: { '1': 'Low', '100': 'High' },
            order: 1,
          },
        },
      },
    };

    const values: ModelParameterValues = { quality: 80 };
    const onChange = vi.fn();

    render(
      <ModelParameterControls
        model={modelWithCustom}
        values={values}
        onChange={onChange}
      />
    );

    // Custom label should be used
    expect(screen.getByText('Output Quality')).toBeInTheDocument();

    // Slider marks should be rendered
    expect(screen.getByText('Low')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('should call onChange when parameter value changes', () => {
    const values: ModelParameterValues = { quality: 80, format: 'png' };
    const onChange = vi.fn();

    render(
      <ModelParameterControls
        model={mockModel}
        values={values}
        onChange={onChange}
      />
    );

    // Change slider value
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '90' } });

    expect(onChange).toHaveBeenCalledWith({
      quality: 90,
      format: 'png',
    });
  });

  it('should sort parameters by order', () => {
    const modelWithOrder: ModelInfo = {
      ...mockModel,
      custom: {
        ui_controls: {
          quality: { type: 'slider', order: 2 },
          format: { type: 'radio', order: 1 },
        },
      },
    };

    const values: ModelParameterValues = { quality: 80, format: 'png' };
    const onChange = vi.fn();

    const { container } = render(
      <ModelParameterControls
        model={modelWithOrder}
        values={values}
        onChange={onChange}
      />
    );

    const items = container.querySelectorAll('.parameter-control-item');
    expect(items).toHaveLength(2);

    // Format should be first (order: 1), Quality second (order: 2)
    expect(items[0]).toHaveTextContent('Format');
    expect(items[1]).toHaveTextContent('Quality');
  });

  it('should not render if no visible parameters', () => {
    const modelNoParams: ModelInfo = {
      ...mockModel,
      schema: {
        parameters: [
          {
            name: 'seed',
            type: 'integer',
            required: false,
            description: 'Seed',
            ui_hidden: true,
          },
        ],
      },
    };

    const values: ModelParameterValues = {};
    const onChange = vi.fn();

    const { container } = render(
      <ModelParameterControls
        model={modelNoParams}
        values={values}
        onChange={onChange}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should not render if no schema', () => {
    const modelNoSchema: ModelInfo = {
      id: 'simple-model',
      name: 'Simple Model',
      model: 'simple/model',
      category: 'restore',
      description: 'Simple model',
    };

    const values: ModelParameterValues = {};
    const onChange = vi.fn();

    const { container } = render(
      <ModelParameterControls
        model={modelNoSchema}
        values={values}
        onChange={onChange}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should disable all inputs when disabled prop is true', () => {
    const values: ModelParameterValues = { quality: 80, format: 'png' };
    const onChange = vi.fn();

    render(
      <ModelParameterControls
        model={mockModel}
        values={values}
        onChange={onChange}
        disabled={true}
      />
    );

    const slider = screen.getByRole('slider');
    const radioButtons = screen.getAllByRole('radio');

    expect(slider).toBeDisabled();
    radioButtons.forEach((radio) => {
      expect(radio).toBeDisabled();
    });
  });

  it('should use default values when no value provided', () => {
    const values: ModelParameterValues = {}; // Empty values
    const onChange = vi.fn();

    render(
      <ModelParameterControls
        model={mockModel}
        values={values}
        onChange={onChange}
      />
    );

    // Should use default from schema
    const slider = screen.getByRole('slider') as HTMLInputElement;
    expect(slider.value).toBe('80');
  });

  it('should handle null model gracefully', () => {
    const values: ModelParameterValues = {};
    const onChange = vi.fn();

    const { container } = render(
      <ModelParameterControls
        model={null as any}
        values={values}
        onChange={onChange}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should handle malformed schema gracefully', () => {
    const malformedModel: ModelInfo = {
      ...mockModel,
      schema: {
        parameters: 'not-an-array' as any,
      },
    };

    const values: ModelParameterValues = {};
    const onChange = vi.fn();

    const { container } = render(
      <ModelParameterControls
        model={malformedModel}
        values={values}
        onChange={onChange}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should skip invalid parameters', () => {
    const modelWithInvalidParam: ModelInfo = {
      ...mockModel,
      schema: {
        parameters: [
          {
            name: 'quality',
            type: 'integer',
            required: false,
            description: 'Valid param',
            default: 80,
            ui_hidden: false,
          },
          null as any, // Invalid parameter
          {
            name: 'format',
            type: 'enum',
            required: false,
            description: 'Another valid param',
            values: ['jpg', 'png'],
            ui_hidden: false,
          },
        ],
      },
    };

    const values: ModelParameterValues = {};
    const onChange = vi.fn();

    render(
      <ModelParameterControls
        model={modelWithInvalidParam}
        values={values}
        onChange={onChange}
      />
    );

    // Should render 2 valid parameters, skip the null one
    expect(screen.getByText('Quality')).toBeInTheDocument();
    expect(screen.getByText('Format')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Count badge
  });
});
