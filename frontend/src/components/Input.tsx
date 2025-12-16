/**
 * Input component with sqowe brand styling
 * Supports text, email, password, and textarea types with validation
 */

import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helpText?: string;
  fullWidth?: boolean;
}

export interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helpText?: string;
  fullWidth?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helpText,
  fullWidth = false,
  id,
  className = '',
  required,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const hasError = Boolean(error);

  return (
    <div className={`form-group ${fullWidth ? 'form-group-full-width' : ''}`}>
      {label && (
        <label htmlFor={inputId} className="form-label">
          {label}
          {required && <span className="form-required"> *</span>}
        </label>
      )}
      <input
        id={inputId}
        className={`form-input ${hasError ? 'form-input-error' : ''} ${className}`}
        aria-invalid={hasError}
        aria-describedby={
          hasError
            ? `${inputId}-error`
            : helpText
            ? `${inputId}-help`
            : undefined
        }
        required={required}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="form-error" role="alert">
          {error}
        </p>
      )}
      {helpText && !error && (
        <p id={`${inputId}-help`} className="form-help">
          {helpText}
        </p>
      )}
    </div>
  );
};

export const TextArea: React.FC<TextAreaProps> = ({
  label,
  error,
  helpText,
  fullWidth = false,
  id,
  className = '',
  required,
  ...props
}) => {
  const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
  const hasError = Boolean(error);

  return (
    <div className={`form-group ${fullWidth ? 'form-group-full-width' : ''}`}>
      {label && (
        <label htmlFor={textareaId} className="form-label">
          {label}
          {required && <span className="form-required"> *</span>}
        </label>
      )}
      <textarea
        id={textareaId}
        className={`form-textarea ${hasError ? 'form-input-error' : ''} ${className}`}
        aria-invalid={hasError}
        aria-describedby={
          hasError
            ? `${textareaId}-error`
            : helpText
            ? `${textareaId}-help`
            : undefined
        }
        required={required}
        {...props}
      />
      {error && (
        <p id={`${textareaId}-error`} className="form-error" role="alert">
          {error}
        </p>
      )}
      {helpText && !error && (
        <p id={`${textareaId}-help`} className="form-help">
          {helpText}
        </p>
      )}
    </div>
  );
};
