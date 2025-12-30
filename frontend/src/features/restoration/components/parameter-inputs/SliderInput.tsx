/**
 * Slider input component for ranged numeric parameters
 */
import React from 'react';
import './ParameterInput.css';

export interface SliderInputProps {
  label: string;
  help?: string;
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
  min: number;
  max: number;
  step?: number;
  marks?: Record<string, string>;
}

export const SliderInput: React.FC<SliderInputProps> = ({
  label,
  help,
  value,
  onChange,
  disabled = false,
  min,
  max,
  step = 1,
  marks,
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
        <span className="parameter-input-value">{value}</span>
      </label>

      <div className="slider-input">
        <input
          type="range"
          className="slider-input-range"
          value={value}
          onChange={handleChange}
          disabled={disabled}
          min={min}
          max={max}
          step={step}
        />

        {marks && (
          <div className="slider-input-marks">
            {Object.entries(marks).map(([markValue, markLabel]) => (
              <span key={markValue} className="slider-mark">
                {markLabel}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
