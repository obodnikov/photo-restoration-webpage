import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useModelConfig } from '../hooks/useModelConfig';
import * as modelConfigService from '../services/modelConfigService';
import type {
  ModelConfigListItem,
  ModelConfigCreate,
  ModelConfigUpdate,
  AvailableTagsResponse,
} from '../types';

// Mock the model config service
vi.mock('../services/modelConfigService', () => ({
  listModelConfigs: vi.fn(),
  getModelConfig: vi.fn(),
  createModelConfig: vi.fn(),
  updateModelConfig: vi.fn(),
  deleteModelConfig: vi.fn(),
  getAvailableTags: vi.fn(),
  validateModelConfig: vi.fn(),
  reloadModelConfigs: vi.fn(),
}));

describe('useModelConfig', () => {
  const mockConfigs: ModelConfigListItem[] = [
    {
      id: 'test-model-1',
      name: 'Test Model 1',
      provider: 'replicate',
      category: 'restore',
      enabled: true,
      source: 'local',
      tags: ['restore', 'fast'],
      version: 'v1.0',
    },
    {
      id: 'test-model-2',
      name: 'Test Model 2',
      provider: 'huggingface',
      category: 'upscale',
      enabled: false,
      source: 'default',
      tags: ['upscale'],
    },
  ];

  const mockAvailableTags: AvailableTagsResponse = {
    tags: ['restore', 'upscale', 'enhance', 'fast', 'advanced'],
    categories: ['restore', 'upscale', 'enhance'],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(modelConfigService.listModelConfigs).mockResolvedValue(mockConfigs);
    vi.mocked(modelConfigService.getAvailableTags).mockResolvedValue(mockAvailableTags);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Initial State', () => {
    it('initializes with correct default state', async () => {
      const { result } = renderHook(() => useModelConfig());

      // Initially loading
      expect(result.current.configs).toEqual([]);
      expect(result.current.availableTags).toBeNull();
      expect(result.current.error).toBeNull();

      // Wait for loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('loads configs and tags on mount', async () => {
      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.configs).toEqual(mockConfigs);
        expect(result.current.availableTags).toEqual(mockAvailableTags);
      });

      expect(modelConfigService.listModelConfigs).toHaveBeenCalledTimes(1);
      expect(modelConfigService.getAvailableTags).toHaveBeenCalledTimes(1);
    });
  });

  describe('Loading State', () => {
    it('sets loading state while fetching configs', async () => {
      let resolveConfigs: (value: ModelConfigListItem[]) => void;
      const configsPromise = new Promise<ModelConfigListItem[]>((resolve) => {
        resolveConfigs = resolve;
      });
      vi.mocked(modelConfigService.listModelConfigs).mockReturnValue(configsPromise);

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });

      resolveConfigs!(mockConfigs);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });
  });

  describe('Error Handling', () => {
    it('handles error when loading configs fails', async () => {
      const error = new Error('Failed to load configs');
      vi.mocked(modelConfigService.listModelConfigs).mockRejectedValue(error);

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to load model configurations');
        expect(result.current.configs).toEqual([]);
      });
    });

    it('continues loading tags even if configs fail', async () => {
      vi.mocked(modelConfigService.listModelConfigs).mockRejectedValue(
        new Error('Config error')
      );

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.availableTags).toEqual(mockAvailableTags);
      });
    });
  });

  describe('Create Config', () => {
    it('creates a new config and reloads the list', async () => {
      const newConfig: ModelConfigCreate = {
        id: 'new-model',
        name: 'New Model',
        model: 'test/model:hash',
        provider: 'replicate',
        category: 'restore',
        enabled: true,
      };

      vi.mocked(modelConfigService.createModelConfig).mockResolvedValue({
        ...newConfig,
        tags: [],
        parameters: {},
        source: 'local',
        description: '',
      });

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.configs).toEqual(mockConfigs);
      });

      await result.current.createConfig(newConfig);

      await waitFor(() => {
        expect(modelConfigService.createModelConfig).toHaveBeenCalledWith(newConfig);
        expect(modelConfigService.listModelConfigs).toHaveBeenCalledTimes(2);
      });
    });

    it('handles error when create fails', async () => {
      const newConfig: ModelConfigCreate = {
        id: 'new-model',
        name: 'New Model',
        model: 'test/model:hash',
        provider: 'replicate',
        category: 'restore',
      };

      const error = new Error('Create failed');
      vi.mocked(modelConfigService.createModelConfig).mockRejectedValue(error);

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.configs).toEqual(mockConfigs);
      });

      await expect(result.current.createConfig(newConfig)).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe('Create failed');
      });
    });
  });

  describe('Update Config', () => {
    it('updates an existing config and reloads the list', async () => {
      const updateData: ModelConfigUpdate = {
        name: 'Updated Model',
        enabled: false,
      };

      vi.mocked(modelConfigService.updateModelConfig).mockResolvedValue({
        id: 'test-model-1',
        name: 'Updated Model',
        model: 'test/model:hash',
        provider: 'replicate',
        category: 'restore',
        enabled: false,
        tags: [],
        parameters: {},
        source: 'local',
        description: '',
      });

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.configs).toEqual(mockConfigs);
      });

      await result.current.updateConfig('test-model-1', updateData);

      await waitFor(() => {
        expect(modelConfigService.updateModelConfig).toHaveBeenCalledWith(
          'test-model-1',
          updateData
        );
        expect(modelConfigService.listModelConfigs).toHaveBeenCalledTimes(2);
      });
    });

    it('handles error when update fails', async () => {
      const error = new Error('Update failed');
      vi.mocked(modelConfigService.updateModelConfig).mockRejectedValue(error);

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.configs).toEqual(mockConfigs);
      });

      await expect(result.current.updateConfig('test-model-1', {})).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe('Update failed');
      });
    });
  });

  describe('Delete Config', () => {
    it('deletes a config and reloads the list', async () => {
      vi.mocked(modelConfigService.deleteModelConfig).mockResolvedValue();

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.configs).toEqual(mockConfigs);
      });

      await result.current.deleteConfig('test-model-1');

      await waitFor(() => {
        expect(modelConfigService.deleteModelConfig).toHaveBeenCalledWith('test-model-1');
        expect(modelConfigService.listModelConfigs).toHaveBeenCalledTimes(2);
      });
    });

    it('handles error when delete fails', async () => {
      const error = new Error('Delete failed');
      vi.mocked(modelConfigService.deleteModelConfig).mockRejectedValue(error);

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.configs).toEqual(mockConfigs);
      });

      await expect(result.current.deleteConfig('test-model-1')).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe('Delete failed');
      });
    });
  });

  describe('Reload Configs', () => {
    it('reloads configs from server', async () => {
      vi.mocked(modelConfigService.reloadModelConfigs).mockResolvedValue({
        success: true,
        message: 'Reloaded',
      });

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.configs).toEqual(mockConfigs);
      });

      await result.current.reloadConfigs();

      await waitFor(() => {
        expect(modelConfigService.reloadModelConfigs).toHaveBeenCalledTimes(1);
        expect(modelConfigService.listModelConfigs).toHaveBeenCalledTimes(2);
      });
    });

    it('handles error when reload fails', async () => {
      const error = new Error('Reload failed');
      vi.mocked(modelConfigService.reloadModelConfigs).mockRejectedValue(error);

      const { result } = renderHook(() => useModelConfig());

      await waitFor(() => {
        expect(result.current.configs).toEqual(mockConfigs);
      });

      await expect(result.current.reloadConfigs()).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe('Reload failed');
      });
    });
  });
});
