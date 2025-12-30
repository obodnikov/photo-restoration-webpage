/**
 * Toggle switch component for boolean parameters
 */
import React from 'react';
import './ParameterInput.css';

export interface ToggleInputProps {
  label: string;
  help?: string;
  value: boolean;
  onChange: (value: boolean) => void;
  disabled?: boolean;
  variant?: 'toggle' | 'checkbox';
}

export const ToggleInput: React.FC<ToggleInputProps> = ({
  label,
  help,
  value,
  onChange,
  disabled = false,
  variant = 'toggle',
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.checked);
  };

  if (variant === 'checkbox') {
    return (
      <div className="parameter-input">
        <label className="checkbox-input">
          <input
            type="checkbox"
            checked={value}
            onChange={handleChange}
            disabled={disabled}
          />
          <span className="checkbox-input-label">
            {label}
            {help && (
              <span className="parameter-input-help" title={help}>
                ⓘ
              </span>
            )}
          </span>
        </label>
      </div>
    );
  }

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
      <div className="toggle-input">
        <button
          type="button"
          className={`toggle-switch ${value ? 'active' : ''}`}
          onClick={() => !disabled && onChange(!value)}
          disabled={disabled}
          aria-label={label}
          aria-pressed={value}
        >
          <span className="toggle-switch-thumb" />
        </button>
        <span className="toggle-input-status">{value ? 'ON' : 'OFF'}</span>
      </div>
    </div>
  );
};
