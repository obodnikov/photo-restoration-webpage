/**
 * Radio button component for enum parameters with 2-3 options
 */
import React, { useId } from 'react';
import './ParameterInput.css';

export interface RadioInputProps {
  label: string;
  help?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  options: string[];
  name?: string; // Unique identifier for the parameter
}

export const RadioInput: React.FC<RadioInputProps> = ({
  label,
  help,
  value,
  onChange,
  disabled = false,
  options,
  name,
}) => {
  // Generate unique ID for this radio group to prevent conflicts
  const uniqueId = useId();
  const radioGroupName = name || `radio-${uniqueId}`;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
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
      <div className="radio-input">
        {options.map((option) => (
          <label key={option} className="radio-input-option">
            <input
              type="radio"
              name={radioGroupName}
              value={option}
              checked={value === option}
              onChange={handleChange}
              disabled={disabled}
            />
            <span className="radio-input-label">{option}</span>
          </label>
        ))}
      </div>
    </div>
  );
};
