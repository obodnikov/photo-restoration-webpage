import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as api from '../../../services/apiClient';
import * as modelConfigService from '../services/modelConfigService';
import type {
  ModelConfigListItem,
  ModelConfigDetail,
  ModelConfigCreate,
  ModelConfigUpdate,
} from '../types';

// Mock the API client
vi.mock('../../../services/apiClient', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}));

describe('modelConfigService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('listModelConfigs', () => {
    it('calls GET endpoint and returns list of configs', async () => {
      const mockConfigs: ModelConfigListItem[] = [
        {
          id: 'test-1',
          name: 'Test Model 1',
          provider: 'replicate',
          category: 'restore',
          enabled: true,
          source: 'local',
          tags: ['restore'],
        },
      ];

      vi.mocked(api.get).mockResolvedValue(mockConfigs);

      const result = await modelConfigService.listModelConfigs();

      expect(api.get).toHaveBeenCalledWith('/admin/models/config');
      expect(result).toEqual(mockConfigs);
    });
  });

  describe('getModelConfig', () => {
    it('calls GET endpoint with model ID and returns config detail', async () => {
      const mockConfig: ModelConfigDetail = {
        id: 'test-1',
        name: 'Test Model',
        model: 'test/model:hash',
        provider: 'replicate',
        category: 'restore',
        description: 'Test description',
        enabled: true,
        tags: ['restore', 'fast'],
        version: 'v1.0',
        parameters: {},
        source: 'local',
      };

      vi.mocked(api.get).mockResolvedValue(mockConfig);

      const result = await modelConfigService.getModelConfig('test-1');

      expect(api.get).toHaveBeenCalledWith('/admin/models/config/test-1');
      expect(result).toEqual(mockConfig);
    });
  });

  describe('createModelConfig', () => {
    it('calls POST endpoint with config data', async () => {
      const newConfig: ModelConfigCreate = {
        id: 'new-model',
        name: 'New Model',
        model: 'test/model:hash',
        provider: 'replicate',
        category: 'restore',
        enabled: true,
      };

      const createdConfig: ModelConfigDetail = {
        ...newConfig,
        description: '',
        tags: [],
        parameters: {},
        source: 'local',
      };

      vi.mocked(api.post).mockResolvedValue(createdConfig);

      const result = await modelConfigService.createModelConfig(newConfig);

      expect(api.post).toHaveBeenCalledWith('/admin/models/config', newConfig);
      expect(result).toEqual(createdConfig);
    });
  });

  describe('updateModelConfig', () => {
    it('calls PUT endpoint with model ID and update data', async () => {
      const updateData: ModelConfigUpdate = {
        name: 'Updated Name',
        enabled: false,
      };

      const updatedConfig: ModelConfigDetail = {
        id: 'test-1',
        name: 'Updated Name',
        model: 'test/model:hash',
        provider: 'replicate',
        category: 'restore',
        description: '',
        enabled: false,
        tags: [],
        parameters: {},
        source: 'local',
      };

      vi.mocked(api.put).mockResolvedValue(updatedConfig);

      const result = await modelConfigService.updateModelConfig('test-1', updateData);

      expect(api.put).toHaveBeenCalledWith('/admin/models/config/test-1', updateData);
      expect(result).toEqual(updatedConfig);
    });
  });

  describe('deleteModelConfig', () => {
    it('calls DELETE endpoint with model ID', async () => {
      vi.mocked(api.del).mockResolvedValue(undefined);

      await modelConfigService.deleteModelConfig('test-1');

      expect(api.del).toHaveBeenCalledWith('/admin/models/config/test-1');
    });
  });

  describe('getAvailableTags', () => {
    it('calls GET endpoint and returns tags and categories', async () => {
      const mockTags = {
        tags: ['restore', 'upscale', 'enhance'],
        categories: ['restore', 'upscale', 'enhance'],
      };

      vi.mocked(api.get).mockResolvedValue(mockTags);

      const result = await modelConfigService.getAvailableTags();

      expect(api.get).toHaveBeenCalledWith('/admin/models/tags');
      expect(result).toEqual(mockTags);
    });
  });

  describe('validateModelConfig', () => {
    it('calls POST endpoint with config data and returns validation result', async () => {
      const configToValidate = {
        id: 'test',
        name: 'Test',
        model: 'test/model',
      };

      const validationResult = {
        valid: true,
        errors: [],
      };

      vi.mocked(api.post).mockResolvedValue(validationResult);

      const result = await modelConfigService.validateModelConfig(configToValidate);

      expect(api.post).toHaveBeenCalledWith('/admin/models/validate', configToValidate);
      expect(result).toEqual(validationResult);
    });

    it('returns validation errors for invalid config', async () => {
      const configToValidate = {
        id: 'test',
        name: '',
      };

      const validationResult = {
        valid: false,
        errors: [{ field: 'name', message: 'Name is required' }],
      };

      vi.mocked(api.post).mockResolvedValue(validationResult);

      const result = await modelConfigService.validateModelConfig(configToValidate);

      expect(result.valid).toBe(false);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].field).toBe('name');
    });
  });

  describe('reloadModelConfigs', () => {
    it('calls POST endpoint to reload configs', async () => {
      const reloadResult = {
        success: true,
        message: 'Configurations reloaded successfully',
      };

      vi.mocked(api.post).mockResolvedValue(reloadResult);

      const result = await modelConfigService.reloadModelConfigs();

      expect(api.post).toHaveBeenCalledWith('/admin/models/reload', {});
      expect(result).toEqual(reloadResult);
    });
  });
});
