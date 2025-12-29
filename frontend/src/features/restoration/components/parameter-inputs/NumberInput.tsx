/**
 * Number input component for numeric parameters
 */
import React from 'react';
import './ParameterInput.css';

export interface NumberInputProps {
  label: string;
  help?: string;
  value: number | null;
  onChange: (value: number | null) => void;
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
    const inputValue = e.target.value;

    // Allow empty string (user is clearing the field)
    if (inputValue === '') {
      onChange(null);
      return;
    }

    const newValue = parseFloat(inputValue);
    if (!isNaN(newValue)) {
      onChange(newValue);
    }
    // If NaN but not empty, keep current value (invalid intermediate state)
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
        value={value ?? ''}
        onChange={handleChange}
        disabled={disabled}
        min={min}
        max={max}
        step={step}
      />
    </div>
  );
};
