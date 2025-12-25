/**
 * Admin Model Configuration Page
 * Main page for managing AI model configurations
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useModelConfig } from '../hooks/useModelConfig';
import { ModelConfigDialog } from '../components/ModelConfigDialog';
import { DeleteModelConfigDialog } from '../components/DeleteModelConfigDialog';
import { Button } from '../../../components/Button';
import { Loader } from '../../../components/Loader';
import { ErrorMessage } from '../../../components/ErrorMessage';
import * as modelConfigService from '../services/modelConfigService';
import type {
  ModelConfigListItem,
  ModelConfigDetail,
  ModelConfigCreate,
  ModelConfigUpdate,
} from '../types';

export const AdminModelConfigPage: React.FC = () => {
  const {
    configs,
    availableTags,
    isLoading,
    error,
    createConfig,
    updateConfig,
    deleteConfig,
    reloadConfigs,
  } = useModelConfig();

  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<ModelConfigDetail | null>(null);
  const [configToDelete, setConfigToDelete] = useState<ModelConfigListItem | null>(null);

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [filterProvider, setFilterProvider] = useState<string>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterSource, setFilterSource] = useState<string>('all');

  // Loading states for operations
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isReloading, setIsReloading] = useState(false);

  // Filter configs
  const filteredConfigs = useMemo(() => {
    return configs.filter((config) => {
      const matchesSearch =
        searchTerm === '' ||
        config.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        config.id.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesProvider = filterProvider === 'all' || config.provider === filterProvider;
      const matchesCategory = filterCategory === 'all' || config.category === filterCategory;
      const matchesSource = filterSource === 'all' || config.source === filterSource;

      return matchesSearch && matchesProvider && matchesCategory && matchesSource;
    });
  }, [configs, searchTerm, filterProvider, filterCategory, filterSource]);

  // Get unique providers and categories for filters
  const { providers, categories } = useMemo(() => {
    const providerSet = new Set<string>();
    const categorySet = new Set<string>();

    configs.forEach((config) => {
      providerSet.add(config.provider);
      categorySet.add(config.category);
    });

    return {
      providers: Array.from(providerSet),
      categories: Array.from(categorySet),
    };
  }, [configs]);

  const handleCreateConfig = useCallback(
    async (_modelId: string, configData: ModelConfigCreate | ModelConfigUpdate) => {
      setIsCreating(true);
      try {
        await createConfig(configData as ModelConfigCreate);
        setIsCreateDialogOpen(false);
      } finally {
        setIsCreating(false);
      }
    },
    [createConfig]
  );

  const handleUpdateConfig = useCallback(
    async (modelId: string, configData: ModelConfigCreate | ModelConfigUpdate) => {
      setIsUpdating(true);
      try {
        await updateConfig(modelId, configData as ModelConfigUpdate);
        setIsEditDialogOpen(false);
        setSelectedConfig(null);
      } finally {
        setIsUpdating(false);
      }
    },
    [updateConfig]
  );

  const handleDeleteConfig = useCallback(
    async (modelId: string) => {
      setIsDeleting(true);
      try {
        await deleteConfig(modelId);
        setIsDeleteDialogOpen(false);
        setConfigToDelete(null);
      } finally {
        setIsDeleting(false);
      }
    },
    [deleteConfig]
  );

  const handleReload = useCallback(async () => {
    setIsReloading(true);
    try {
      await reloadConfigs();
    } finally {
      setIsReloading(false);
    }
  }, [reloadConfigs]);

  const handleEdit = useCallback(async (config: ModelConfigListItem) => {
    try {
      const fullConfig = await modelConfigService.getModelConfig(config.id);
      setSelectedConfig(fullConfig);
      setIsEditDialogOpen(true);
    } catch (err) {
      console.error('Failed to load config details:', err);
    }
  }, []);

  const handleDelete = useCallback((config: ModelConfigListItem) => {
    setConfigToDelete(config);
    setIsDeleteDialogOpen(true);
  }, []);

  const handleCloseCreateDialog = useCallback(() => {
    setIsCreateDialogOpen(false);
  }, []);

  const handleCloseEditDialog = useCallback(() => {
    setIsEditDialogOpen(false);
    setSelectedConfig(null);
  }, []);

  const handleCloseDeleteDialog = useCallback(() => {
    setIsDeleteDialogOpen(false);
    setConfigToDelete(null);
  }, []);

  return (
    <div className="admin-model-config-page">
      <div className="container">
        <div className="page-header">
          <div className="page-title-section">
            <h1 className="page-title">Model Configuration</h1>
            <p className="page-subtitle">
              Manage AI model configurations and settings
            </p>
          </div>

          <Button
            variant="primary"
            size="medium"
            onClick={() => setIsCreateDialogOpen(true)}
          >
            + Add Model
          </Button>
        </div>

        {error && <ErrorMessage message={error} title="Error Loading Configurations" />}

        {/* Controls */}
        <div className="controls-bar">
          <div className="controls-left">
            <input
              type="text"
              className="search-input"
              placeholder="Search by name or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <select
              className="filter-dropdown"
              value={filterProvider}
              onChange={(e) => setFilterProvider(e.target.value)}
            >
              <option value="all">All Providers</option>
              {providers.map((provider) => (
                <option key={provider} value={provider}>
                  {provider}
                </option>
              ))}
            </select>
            <select
              className="filter-dropdown"
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
            <select
              className="filter-dropdown"
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
            >
              <option value="all">All Sources</option>
              <option value="local">Local</option>
              <option value="default">Default</option>
              <option value="production">Production</option>
            </select>
          </div>
          <div className="controls-right">
            <Button
              variant="secondary"
              size="small"
              onClick={handleReload}
              loading={isReloading}
            >
              Reload
            </Button>
          </div>
        </div>

        {/* Config List */}
        {isLoading && configs.length === 0 ? (
          <Loader text="Loading configurations..." />
        ) : filteredConfigs.length === 0 ? (
          <div className="config-empty-state">
            <h3>No configurations found</h3>
            <p>
              {searchTerm || filterProvider !== 'all' || filterCategory !== 'all' || filterSource !== 'all'
                ? 'Try adjusting your filters'
                : 'Click "Add Model" to create your first configuration'}
            </p>
          </div>
        ) : (
          <div className="config-list">
            {filteredConfigs.map((config) => (
              <div key={config.id} className="config-card">
                <div className="config-header">
                  <h3>{config.name}</h3>
                  <span className={`badge badge-${config.source}`}>
                    {config.source}
                  </span>
                </div>

                <div className="config-meta">
                  <div className="config-meta-item">
                    <span className="config-meta-label">ID:</span>
                    <span>{config.id}</span>
                  </div>
                  <div className="config-meta-item">
                    <span className="config-meta-label">Provider:</span>
                    <span>{config.provider}</span>
                  </div>
                  <div className="config-meta-item">
                    <span className="config-meta-label">Category:</span>
                    <span>{config.category}</span>
                  </div>
                  {config.version && (
                    <div className="config-meta-item">
                      <span className="config-meta-label">Version:</span>
                      <span>{config.version}</span>
                    </div>
                  )}
                  <div className="config-meta-item">
                    <span className="config-meta-label">Status:</span>
                    <span className={config.enabled ? 'badge-success' : 'badge-inactive'}>
                      {config.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>

                <div className="config-tags">
                  {config.tags && config.tags.length > 0 ? (
                    config.tags.map((tag) => (
                      <span key={tag} className="config-tag">
                        {tag}
                      </span>
                    ))
                  ) : (
                    <span className="config-tag" style={{ opacity: 0.5 }}>
                      No tags
                    </span>
                  )}
                </div>

                <div className="config-actions">
                  <Button
                    variant="secondary"
                    size="small"
                    onClick={() => handleEdit(config)}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    size="small"
                    onClick={() => handleDelete(config)}
                    disabled={config.source !== 'local'}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Dialogs */}
        <ModelConfigDialog
          isOpen={isCreateDialogOpen}
          onClose={handleCloseCreateDialog}
          onSave={handleCreateConfig}
          availableTags={availableTags?.tags || []}
          availableCategories={availableTags?.categories || []}
          isLoading={isCreating}
        />

        <ModelConfigDialog
          isOpen={isEditDialogOpen}
          onClose={handleCloseEditDialog}
          onSave={handleUpdateConfig}
          config={selectedConfig}
          availableTags={availableTags?.tags || []}
          availableCategories={availableTags?.categories || []}
          isLoading={isUpdating}
        />

        <DeleteModelConfigDialog
          isOpen={isDeleteDialogOpen}
          onClose={handleCloseDeleteDialog}
          onConfirm={handleDeleteConfig}
          config={configToDelete}
          isLoading={isDeleting}
        />
      </div>
    </div>
  );
};
