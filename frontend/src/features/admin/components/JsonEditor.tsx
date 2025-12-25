/**
 * JSON Editor Component
 * Simple multiline textarea for editing JSON with tab key support and validation
 */

import React, { useRef, useState, useEffect, KeyboardEvent } from 'react';

export interface JsonEditorProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  error?: string;
  disabled?: boolean;
}

export const JsonEditor: React.FC<JsonEditorProps> = ({
  label,
  value,
  onChange,
  placeholder = '{}',
  rows = 10,
  error,
  disabled = false,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Validate JSON on value change
  useEffect(() => {
    if (!value.trim()) {
      setValidationError(null);
      return;
    }

    try {
      JSON.parse(value);
      setValidationError(null);
    } catch (err) {
      if (err instanceof Error) {
        setValidationError(err.message);
      } else {
        setValidationError('Invalid JSON syntax');
      }
    }
  }, [value]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Handle Tab key for indentation
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = e.currentTarget;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newValue = value.substring(0, start) + '  ' + value.substring(end);

      onChange(newValue);

      // Set cursor position after the inserted tab
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2;
      }, 0);
    }
  };

  // Use parent error if provided, otherwise use internal validation error
  const displayError = error || validationError;

  return (
    <div className="json-editor-container">
      <label className="json-editor-label">{label}</label>
      <textarea
        ref={textareaRef}
        className={`json-editor ${displayError ? 'json-editor-error' : ''}`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={rows}
        disabled={disabled}
        spellCheck={false}
      />
      {displayError && <div className="json-error-message">{displayError}</div>}
    </div>
  );
};
