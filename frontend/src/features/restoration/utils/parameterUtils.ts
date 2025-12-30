/**
 * Utilities for parameter UI configuration
 */
import type {
  ParameterSchema,
  ModelInfo,
  UIControlConfig,
  ModelParameterValues,
} from '../types';

/**
 * Get UI configuration for a parameter
 *
 * Priority:
 * 1. Custom ui_controls (if specified in model.custom)
 * 2. Auto-detection from parameter schema
 *
 * NOTE: This function is pure and side-effect free. It's already memoized
 * at the component level where it's used (ModelParameterControls useMemo).
 * No additional memoization needed.
 *
 * @param paramName - Parameter name
 * @param param - Parameter schema
 * @param model - Model information
 * @returns UI control configuration, or null if parameter should be hidden
 */
export function getParameterUIConfig(
  paramName: string,
  param: ParameterSchema,
  model: ModelInfo
): UIControlConfig | null {
  // Hidden parameters → return null
  if (param.ui_hidden) {
    return null;
  }

  // Check custom UI config (explicit override)
  if (model.custom?.ui_controls?.[paramName]) {
    return model.custom.ui_controls[paramName];
  }

  // Auto-detect from schema
  return autoDetectUIControl(param);
}

/**
 * Auto-detect UI control type from parameter schema
 *
 * Logic:
 * - boolean → toggle
 * - enum with 2-3 values → radio
 * - enum with 4+ values → dropdown
 * - integer/float with min & max → slider
 * - integer/float without range → number
 * - string → text
 *
 * @param param - Parameter schema
 * @returns UI control configuration
 */
export function autoDetectUIControl(
  param: ParameterSchema
): UIControlConfig {
  // Boolean → toggle
  if (param.type === 'boolean') {
    return { type: 'toggle' };
  }

  // Enum → radio (2-3 options) or dropdown (4+)
  if (param.type === 'enum' && param.values) {
    const type = param.values.length <= 3 ? 'radio' : 'dropdown';
    return { type, options: param.values };
  }

  // Numeric with range → slider
  if (
    (param.type === 'integer' || param.type === 'float') &&
    param.min != null &&
    param.max != null
  ) {
    return { type: 'slider' };
  }

  // Numeric without range → number input
  if (param.type === 'integer' || param.type === 'float') {
    return { type: 'number' };
  }

  // String → text input
  return { type: 'text' };
}

/**
 * Get default parameter values from model schema
 *
 * Extracts default values for all visible (ui_hidden=false) parameters
 *
 * @param model - Model information
 * @returns Object with parameter names and their default values
 */
export function getDefaultParameterValues(
  model: ModelInfo
): ModelParameterValues {
  if (!model.schema?.parameters) {
    return {};
  }

  const defaults: ModelParameterValues = {};

  model.schema.parameters.forEach((param) => {
    // Only include visible parameters with defaults
    if (!param.ui_hidden && param.default !== undefined) {
      defaults[param.name] = param.default;
    }
  });

  return defaults;
}

/**
 * Format parameter name to human-readable label
 *
 * Converts snake_case to Title Case
 * Example: "output_format" → "Output Format"
 *
 * @param paramName - Parameter name in snake_case
 * @returns Formatted label in Title Case
 */
export function formatParameterLabel(paramName: string): string {
  return paramName
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
