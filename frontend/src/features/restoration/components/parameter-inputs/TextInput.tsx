/**
 * Text input component for string parameters
 */
import React from 'react';
import './ParameterInput.css';

export interface TextInputProps {
  label: string;
  help?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  multiline?: boolean;
}

export const TextInput: React.FC<TextInputProps> = ({
  label,
  help,
  value,
  onChange,
  disabled = false,
  multiline = false,
}) => {
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
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
      {multiline ? (
        <textarea
          className="parameter-input-textarea"
          value={value}
          onChange={handleChange}
          disabled={disabled}
          rows={3}
        />
      ) : (
        <input
          type="text"
          className="parameter-input-field"
          value={value}
          onChange={handleChange}
          disabled={disabled}
        />
      )}
    </div>
  );
};
