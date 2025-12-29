/**
 * Dropdown select component for enum parameters with 4+ options
 */
import React from 'react';
import './ParameterInput.css';

export interface DropdownInputProps {
  label: string;
  help?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  options: string[];
}

export const DropdownInput: React.FC<DropdownInputProps> = ({
  label,
  help,
  value,
  onChange,
  disabled = false,
  options,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
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
      <select
        className="parameter-input-select"
        value={value}
        onChange={handleChange}
        disabled={disabled}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </div>
  );
};
