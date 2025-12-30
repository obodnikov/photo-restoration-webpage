/**
 * Tests for parameter utilities
 */
import { describe, it, expect } from 'vitest';
import {
  getParameterUIConfig,
  autoDetectUIControl,
  getDefaultParameterValues,
  formatParameterLabel,
} from '../parameterUtils';
import type { ParameterSchema, ModelInfo } from '../../types';

describe('parameterUtils', () => {
  describe('autoDetectUIControl', () => {
    it('should detect toggle for boolean parameters', () => {
      const param: ParameterSchema = {
        name: 'enable_feature',
        type: 'boolean',
        required: false,
        description: 'Enable feature',
        default: true,
        ui_hidden: false,
      };

      const config = autoDetectUIControl(param);
      expect(config.type).toBe('toggle');
    });

    it('should detect radio for enum with 2-3 values', () => {
      const param: ParameterSchema = {
        name: 'format',
        type: 'enum',
        required: false,
        description: 'Format',
        values: ['jpg', 'png'],
        ui_hidden: false,
      };

      const config = autoDetectUIControl(param);
      expect(config.type).toBe('radio');
      expect(config.options).toEqual(['jpg', 'png']);
    });

    it('should detect dropdown for enum with 4+ values', () => {
      const param: ParameterSchema = {
        name: 'format',
        type: 'enum',
        required: false,
        description: 'Format',
        values: ['jpg', 'png', 'webp', 'gif'],
        ui_hidden: false,
      };

      const config = autoDetectUIControl(param);
      expect(config.type).toBe('dropdown');
      expect(config.options).toEqual(['jpg', 'png', 'webp', 'gif']);
    });

    it('should detect slider for integer with min and max', () => {
      const param: ParameterSchema = {
        name: 'quality',
        type: 'integer',
        required: false,
        description: 'Quality',
        min: 1,
        max: 100,
        ui_hidden: false,
      };

      const config = autoDetectUIControl(param);
      expect(config.type).toBe('slider');
    });

    it('should detect slider for float with min and max', () => {
      const param: ParameterSchema = {
        name: 'threshold',
        type: 'float',
        required: false,
        description: 'Threshold',
        min: 0.0,
        max: 1.0,
        ui_hidden: false,
      };

      const config = autoDetectUIControl(param);
      expect(config.type).toBe('slider');
    });

    it('should detect number for integer without range', () => {
      const param: ParameterSchema = {
        name: 'iterations',
        type: 'integer',
        required: false,
        description: 'Iterations',
        ui_hidden: false,
      };

      const config = autoDetectUIControl(param);
      expect(config.type).toBe('number');
    });

    it('should detect text for string parameters', () => {
      const param: ParameterSchema = {
        name: 'prompt',
        type: 'string',
        required: false,
        description: 'Prompt',
        ui_hidden: false,
      };

      const config = autoDetectUIControl(param);
      expect(config.type).toBe('text');
    });
  });

  describe('getParameterUIConfig', () => {
    it('should return null for hidden parameters', () => {
      const param: ParameterSchema = {
        name: 'seed',
        type: 'integer',
        required: false,
        description: 'Random seed',
        ui_hidden: true,
      };

      const model: ModelInfo = {
        id: 'test-model',
        name: 'Test Model',
        model: 'test/model',
        category: 'restore',
        description: 'Test',
      };

      const config = getParameterUIConfig('seed', param, model);
      expect(config).toBeNull();
    });

    it('should return custom UI config when specified', () => {
      const param: ParameterSchema = {
        name: 'quality',
        type: 'integer',
        required: false,
        description: 'Quality',
        min: 1,
        max: 100,
        ui_hidden: false,
      };

      const model: ModelInfo = {
        id: 'test-model',
        name: 'Test Model',
        model: 'test/model',
        category: 'restore',
        description: 'Test',
        custom: {
          ui_controls: {
            quality: {
              type: 'number', // Override slider with number
              label: 'Output Quality',
              step: 5,
            },
          },
        },
      };

      const config = getParameterUIConfig('quality', param, model);
      expect(config?.type).toBe('number');
      expect(config?.label).toBe('Output Quality');
      expect(config?.step).toBe(5);
    });

    it('should auto-detect when no custom config provided', () => {
      const param: ParameterSchema = {
        name: 'format',
        type: 'enum',
        required: false,
        description: 'Format',
        values: ['jpg', 'png'],
        ui_hidden: false,
      };

      const model: ModelInfo = {
        id: 'test-model',
        name: 'Test Model',
        model: 'test/model',
        category: 'restore',
        description: 'Test',
      };

      const config = getParameterUIConfig('format', param, model);
      expect(config?.type).toBe('radio');
      expect(config?.options).toEqual(['jpg', 'png']);
    });
  });

  describe('getDefaultParameterValues', () => {
    it('should extract default values from visible parameters', () => {
      const model: ModelInfo = {
        id: 'test-model',
        name: 'Test Model',
        model: 'test/model',
        category: 'restore',
        description: 'Test',
        schema: {
          parameters: [
            {
              name: 'quality',
              type: 'integer',
              required: false,
              description: 'Quality',
              default: 80,
              ui_hidden: false,
            },
            {
              name: 'format',
              type: 'enum',
              required: false,
              description: 'Format',
              default: 'png',
              values: ['jpg', 'png'],
              ui_hidden: false,
            },
            {
              name: 'seed',
              type: 'integer',
              required: false,
              description: 'Seed',
              default: 42,
              ui_hidden: true, // Hidden - should be excluded
            },
          ],
        },
      };

      const defaults = getDefaultParameterValues(model);
      expect(defaults).toEqual({
        quality: 80,
        format: 'png',
        // seed is hidden, so not included
      });
    });

    it('should return empty object when no schema', () => {
      const model: ModelInfo = {
        id: 'test-model',
        name: 'Test Model',
        model: 'test/model',
        category: 'restore',
        description: 'Test',
      };

      const defaults = getDefaultParameterValues(model);
      expect(defaults).toEqual({});
    });

    it('should handle parameters without defaults', () => {
      const model: ModelInfo = {
        id: 'test-model',
        name: 'Test Model',
        model: 'test/model',
        category: 'restore',
        description: 'Test',
        schema: {
          parameters: [
            {
              name: 'quality',
              type: 'integer',
              required: false,
              description: 'Quality',
              ui_hidden: false,
              // No default
            },
          ],
        },
      };

      const defaults = getDefaultParameterValues(model);
      expect(defaults).toEqual({});
    });
  });

  describe('formatParameterLabel', () => {
    it('should format snake_case to Title Case', () => {
      expect(formatParameterLabel('output_format')).toBe('Output Format');
      expect(formatParameterLabel('compression_quality')).toBe('Compression Quality');
      expect(formatParameterLabel('upscale_factor')).toBe('Upscale Factor');
    });

    it('should handle single word', () => {
      expect(formatParameterLabel('quality')).toBe('Quality');
    });

    it('should handle multiple underscores', () => {
      expect(formatParameterLabel('max_file_size_mb')).toBe('Max File Size Mb');
    });
  });
});
