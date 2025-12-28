/**
 * Hook for managing model configurations
 */
import { useState, useEffect, useCallback } from 'react';
import * as modelConfigService from '../services/modelConfigService';
import type {
  ModelConfigListItem,
  ModelConfigCreate,
  ModelConfigUpdate,
  AvailableTagsResponse,
} from '../types';

export const useModelConfig = () => {
  const [configs, setConfigs] = useState<ModelConfigListItem[]>([]);
  const [availableTags, setAvailableTags] = useState<AvailableTagsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConfigs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await modelConfigService.listModelConfigs();
      setConfigs(data);
    } catch (err) {
      setError('Failed to load model configurations');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadAvailableTags = useCallback(async () => {
    try {
      const data = await modelConfigService.getAvailableTags();
      setAvailableTags(data);
    } catch (err) {
      console.error('Failed to load tags:', err);
    }
  }, []);

  const createConfig = useCallback(
    async (config: ModelConfigCreate) => {
      setIsLoading(true);
      setError(null);
      try {
        await modelConfigService.createModelConfig(config);
        await loadConfigs();
      } catch (err: any) {
        setError(err.message || 'Failed to create configuration');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [loadConfigs]
  );

  const updateConfig = useCallback(
    async (modelId: string, config: ModelConfigUpdate) => {
      setIsLoading(true);
      setError(null);
      try {
        await modelConfigService.updateModelConfig(modelId, config);
        await loadConfigs();
      } catch (err: any) {
        setError(err.message || 'Failed to update configuration');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [loadConfigs]
  );

  const deleteConfig = useCallback(
    async (modelId: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await modelConfigService.deleteModelConfig(modelId);
        await loadConfigs();
      } catch (err: any) {
        setError(err.message || 'Failed to delete configuration');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [loadConfigs]
  );

  const reloadConfigs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      await modelConfigService.reloadModelConfigs();
      await loadConfigs();
    } catch (err: any) {
      setError(err.message || 'Failed to reload configurations');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [loadConfigs]);

  useEffect(() => {
    loadConfigs();
    loadAvailableTags();
  }, [loadConfigs, loadAvailableTags]);

  return {
    configs,
    availableTags,
    isLoading,
    error,
    loadConfigs,
    createConfig,
    updateConfig,
    deleteConfig,
    reloadConfigs,
  };
};
