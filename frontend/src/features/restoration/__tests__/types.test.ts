/**
 * Tests for restoration types
 */
import { describe, it, expect } from 'vitest';
import type {
  UIControlType,
  UIControlConfig,
  ParameterSchema,
  ModelSchema,
  ModelCustomConfig,
  ModelParameterValues,
  ModelInfo,
} from '../types';

describe('Restoration Types', () => {
  describe('UIControlConfig', () => {
    it('should accept valid UI control configuration', () => {
      const sliderConfig: UIControlConfig = {
        type: 'slider',
        label: 'Quality',
        help: 'Output quality',
        step: 5,
        marks: { '1': 'Low', '50': 'Medium', '100': 'High' },
        order: 1,
      };

      expect(sliderConfig.type).toBe('slider');
      expect(sliderConfig.label).toBe('Quality');
      expect(sliderConfig.marks).toEqual({ '1': 'Low', '50': 'Medium', '100': 'High' });
    });

    it('should accept minimal UI control configuration', () => {
      const textConfig: UIControlConfig = {
        type: 'text',
      };

      expect(textConfig.type).toBe('text');
      expect(textConfig.label).toBeUndefined();
    });

    it('should accept all UI control types', () => {
      const types: UIControlType[] = [
        'text',
        'textarea',
        'number',
        'slider',
        'dropdown',
        'radio',
        'toggle',
        'checkbox',
      ];

      types.forEach((type) => {
        const config: UIControlConfig = { type };
        expect(config.type).toBe(type);
      });
    });
  });

  describe('ParameterSchema', () => {
    it('should accept parameter schema with all fields', () => {
      const param: ParameterSchema = {
        name: 'quality',
        type: 'integer',
        required: false,
        description: 'Output quality',
        default: 80,
        min: 1,
        max: 100,
        ui_hidden: false,
        ui_group: 'output',
      };

      expect(param.name).toBe('quality');
      expect(param.type).toBe('integer');
      expect(param.default).toBe(80);
    });

    it('should accept parameter schema with enum values', () => {
      const param: ParameterSchema = {
        name: 'format',
        type: 'enum',
        required: false,
        description: 'Output format',
        default: 'png',
        values: ['jpg', 'png'],
        ui_hidden: false,
      };

      expect(param.values).toEqual(['jpg', 'png']);
    });
  });

  describe('ModelCustomConfig', () => {
    it('should accept custom config with ui_controls', () => {
      const custom: ModelCustomConfig = {
        ui_controls: {
          quality: {
            type: 'slider',
            label: 'Quality',
            order: 1,
          },
          format: {
            type: 'dropdown',
            options: ['jpg', 'png'],
            order: 2,
          },
        },
      };

      expect(custom.ui_controls?.quality.type).toBe('slider');
      expect(custom.ui_controls?.format.options).toEqual(['jpg', 'png']);
    });

    it('should accept empty custom config', () => {
      const custom: ModelCustomConfig = {};
      expect(custom.ui_controls).toBeUndefined();
    });

    it('should accept custom config with extra fields', () => {
      const custom: ModelCustomConfig = {
        ui_controls: {
          quality: { type: 'slider' },
        },
        some_other_field: 'value',
      };

      expect(custom.some_other_field).toBe('value');
    });
  });

  describe('ModelParameterValues', () => {
    it('should accept parameter values', () => {
      const values: ModelParameterValues = {
        quality: 85,
        format: 'png',
        enhance: true,
      };

      expect(values.quality).toBe(85);
      expect(values.format).toBe('png');
      expect(values.enhance).toBe(true);
    });

    it('should accept empty parameter values', () => {
      const values: ModelParameterValues = {};
      expect(Object.keys(values)).toHaveLength(0);
    });
  });

  describe('ModelInfo', () => {
    it('should accept model info with schema and custom config', () => {
      const model: ModelInfo = {
        id: 'test-model',
        name: 'Test Model',
        model: 'test/model',
        category: 'restore',
        description: 'Test model',
        schema: {
          parameters: [
            {
              name: 'quality',
              type: 'integer',
              required: false,
              description: 'Quality',
              default: 80,
              min: 1,
              max: 100,
              ui_hidden: false,
            },
          ],
          custom: {
            max_file_size_mb: 10,
            supported_formats: ['jpg', 'png'],
          },
        },
        custom: {
          ui_controls: {
            quality: {
              type: 'slider',
              label: 'Quality',
            },
          },
        },
      };

      expect(model.schema?.parameters).toHaveLength(1);
      expect(model.custom?.ui_controls?.quality.type).toBe('slider');
    });

    it('should accept model info without schema and custom', () => {
      const model: ModelInfo = {
        id: 'simple-model',
        name: 'Simple Model',
        model: 'simple/model',
        category: 'restore',
        description: 'Simple model',
      };

      expect(model.schema).toBeUndefined();
      expect(model.custom).toBeUndefined();
    });
  });
});
