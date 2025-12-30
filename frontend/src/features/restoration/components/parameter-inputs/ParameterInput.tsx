/**
 * Factory component that renders the appropriate input based on UI config
 */
import React from 'react';
import type { ParameterSchema, UIControlConfig } from '../../types';
import { TextInput } from './TextInput';
import { NumberInput } from './NumberInput';
import { SliderInput } from './SliderInput';
import { DropdownInput } from './DropdownInput';
import { RadioInput } from './RadioInput';
import { ToggleInput } from './ToggleInput';
import { formatParameterLabel } from '../../utils/parameterUtils';

export interface ParameterInputProps {
  param: ParameterSchema;
  uiConfig: UIControlConfig;
  value: any;
  onChange: (value: any) => void;
  disabled?: boolean;
}

export const ParameterInput: React.FC<ParameterInputProps> = ({
  param,
  uiConfig,
  value,
  onChange,
  disabled = false,
}) => {
  const label = uiConfig.label || formatParameterLabel(param.name);
  const help = uiConfig.help || param.description;

  switch (uiConfig.type) {
    case 'text':
    case 'textarea':
      return (
        <TextInput
          label={label}
          help={help}
          value={value ?? ''}
          onChange={onChange}
          disabled={disabled}
          multiline={uiConfig.type === 'textarea'}
        />
      );

    case 'number':
      // Only use default when value is truly undefined, not when explicitly null (cleared)
      const numberValue = value !== undefined ? value : (param.default ?? null);
      return (
        <NumberInput
          label={label}
          help={help}
          value={numberValue}
          onChange={onChange}
          disabled={disabled}
          min={param.min}
          max={param.max}
          step={uiConfig.step}
        />
      );

    case 'slider':
      return (
        <SliderInput
          label={label}
          help={help}
          value={value ?? param.min ?? 0}
          onChange={onChange}
          disabled={disabled}
          min={param.min ?? 0}
          max={param.max ?? 100}
          step={uiConfig.step}
          marks={uiConfig.marks}
        />
      );

    case 'dropdown':
      return (
        <DropdownInput
          label={label}
          help={help}
          value={value ?? ''}
          onChange={onChange}
          disabled={disabled}
          options={uiConfig.options || param.values || []}
        />
      );

    case 'radio':
      return (
        <RadioInput
          label={label}
          help={help}
          value={value ?? ''}
          onChange={onChange}
          disabled={disabled}
          options={uiConfig.options || param.values || []}
          name={param.name}
        />
      );

    case 'toggle':
    case 'checkbox':
      return (
        <ToggleInput
          label={label}
          help={help}
          value={value ?? false}
          onChange={onChange}
          disabled={disabled}
          variant={uiConfig.type}
        />
      );

    default:
      // Fallback to text input
      return (
        <TextInput
          label={label}
          help={help}
          value={value ?? ''}
          onChange={onChange}
          disabled={disabled}
        />
      );
  }
};
