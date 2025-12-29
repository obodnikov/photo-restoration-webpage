/**
 * Tests for ParameterInput factory component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ParameterInput } from '../ParameterInput';
import type { ParameterSchema, UIControlConfig } from '../../../types';

describe('ParameterInput', () => {
  const mockOnChange = vi.fn();

  describe('text and textarea', () => {
    it('should render TextInput for text type', () => {
      const param: ParameterSchema = {
        name: 'prompt',
        type: 'string',
        required: false,
        description: 'Prompt text',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'text' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value="test"
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveValue('test');
    });

    it('should render textarea for textarea type', () => {
      const param: ParameterSchema = {
        name: 'description',
        type: 'string',
        required: false,
        description: 'Long text',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'textarea' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value="multiline text"
          onChange={mockOnChange}
        />
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea.tagName).toBe('TEXTAREA');
      expect(textarea).toHaveValue('multiline text');
    });
  });

  describe('number input', () => {
    it('should render NumberInput for number type', () => {
      const param: ParameterSchema = {
        name: 'iterations',
        type: 'integer',
        required: false,
        description: 'Iterations',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'number' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={10}
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('spinbutton');
      expect(input).toHaveValue(10);
    });
  });

  describe('slider input', () => {
    it('should render SliderInput for slider type', () => {
      const param: ParameterSchema = {
        name: 'quality',
        type: 'integer',
        required: false,
        description: 'Quality',
        min: 1,
        max: 100,
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'slider' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={80}
          onChange={mockOnChange}
        />
      );

      const slider = screen.getByRole('slider');
      expect(slider).toHaveValue('80');
    });
  });

  describe('dropdown input', () => {
    it('should render DropdownInput for dropdown type', () => {
      const param: ParameterSchema = {
        name: 'format',
        type: 'enum',
        required: false,
        description: 'Format',
        values: ['jpg', 'png', 'webp', 'gif'],
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'dropdown' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value="png"
          onChange={mockOnChange}
        />
      );

      const select = screen.getByRole('combobox');
      expect(select).toHaveValue('png');
    });
  });

  describe('radio input', () => {
    it('should render RadioInput for radio type', () => {
      const param: ParameterSchema = {
        name: 'mode',
        type: 'enum',
        required: false,
        description: 'Mode',
        values: ['fast', 'quality'],
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'radio' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value="fast"
          onChange={mockOnChange}
        />
      );

      const radios = screen.getAllByRole('radio');
      expect(radios).toHaveLength(2);
      expect(radios[0]).toBeChecked();
    });
  });

  describe('toggle and checkbox', () => {
    it('should render ToggleInput for toggle type', () => {
      const param: ParameterSchema = {
        name: 'enable_feature',
        type: 'boolean',
        required: false,
        description: 'Enable',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'toggle' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={true}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('ON')).toBeInTheDocument();
    });

    it('should render checkbox variant for checkbox type', () => {
      const param: ParameterSchema = {
        name: 'accept_terms',
        type: 'boolean',
        required: false,
        description: 'Accept',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'checkbox' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={true}
          onChange={mockOnChange}
        />
      );

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeChecked();
    });
  });

  describe('custom labels and help text', () => {
    it('should use custom label from uiConfig', () => {
      const param: ParameterSchema = {
        name: 'output_quality',
        type: 'integer',
        required: false,
        description: 'Quality',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = {
        type: 'slider',
        label: 'Custom Quality Label',
      };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={80}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('Custom Quality Label')).toBeInTheDocument();
    });

    it('should format parameter name when no custom label', () => {
      const param: ParameterSchema = {
        name: 'output_quality',
        type: 'integer',
        required: false,
        description: 'Quality',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'slider' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={80}
          onChange={mockOnChange}
        />
      );

      // formatParameterLabel converts snake_case to Title Case
      expect(screen.getByText('Output Quality')).toBeInTheDocument();
    });

    it('should display help text tooltip', () => {
      const param: ParameterSchema = {
        name: 'quality',
        type: 'integer',
        required: false,
        description: 'Default help',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = {
        type: 'slider',
        help: 'Custom help text',
      };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={80}
          onChange={mockOnChange}
        />
      );

      const helpIcon = screen.getByTitle('Custom help text');
      expect(helpIcon).toBeInTheDocument();
    });
  });

  describe('fallback behavior', () => {
    it('should fallback to TextInput for unsupported type', () => {
      const param: ParameterSchema = {
        name: 'custom_param',
        type: 'string',
        required: false,
        description: 'Custom',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = {
        type: 'unsupported' as any,
      };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value="fallback"
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('fallback');
    });
  });

  describe('default values', () => {
    it('should use empty string for undefined text value', () => {
      const param: ParameterSchema = {
        name: 'text',
        type: 'string',
        required: false,
        description: 'Text',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'text' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={undefined}
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('');
    });

    it('should use 0 for undefined number value', () => {
      const param: ParameterSchema = {
        name: 'count',
        type: 'integer',
        required: false,
        description: 'Count',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'number' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={undefined}
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('spinbutton');
      expect(input).toHaveValue(0);
    });

    it('should use false for undefined boolean value', () => {
      const param: ParameterSchema = {
        name: 'enabled',
        type: 'boolean',
        required: false,
        description: 'Enabled',
        ui_hidden: false,
      };

      const uiConfig: UIControlConfig = { type: 'checkbox' };

      render(
        <ParameterInput
          param={param}
          uiConfig={uiConfig}
          value={undefined}
          onChange={mockOnChange}
        />
      );

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).not.toBeChecked();
    });
  });
});
