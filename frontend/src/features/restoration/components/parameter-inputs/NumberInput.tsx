/**
 * Number input component for numeric parameters
 */
import React from 'react';
import './ParameterInput.css';

export interface NumberInputProps {
  label: string;
  help?: string;
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
  min?: number;
  max?: number;
  step?: number;
}

export const NumberInput: React.FC<NumberInputProps> = ({
  label,
  help,
  value,
  onChange,
  disabled = false,
  min,
  max,
  step = 1,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value);
    if (!isNaN(newValue)) {
      onChange(newValue);
    }
  };

  return (
    <div className="parameter-input">
      <label className="parameter-input-label">
        {label}
        {help && (
          <span className="parameter-input-help" title={help}>
            ⓘ
          </span>
        )}
      </label>
      <input
        type="number"
        className="parameter-input-field"
        value={value}
        onChange={handleChange}
        disabled={disabled}
        min={min}
        max={max}
        step={step}
      />
    </div>
  );
};
