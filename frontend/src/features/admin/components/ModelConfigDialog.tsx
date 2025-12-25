/**
 * Model Configuration Create/Edit Dialog
 * Main dialog for creating and editing model configurations
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Modal } from '../../../components/Modal';
import { Button } from '../../../components/Button';
import { ErrorMessage } from '../../../components/ErrorMessage';
import { JsonEditor } from './JsonEditor';
import { JsonPreview } from './JsonPreview';
import { TagSelector } from './TagSelector';
import type {
  ModelConfigDetail,
  ModelConfigCreate,
  ModelConfigUpdate,
  ModelProvider,
} from '../types';

export interface ModelConfigDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (modelId: string, config: ModelConfigCreate | ModelConfigUpdate) => Promise<void>;
  config?: ModelConfigDetail | null;
  availableTags: string[];
  availableCategories: string[];
  isLoading?: boolean;
}

export const ModelConfigDialog: React.FC<ModelConfigDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  config,
  availableTags,
  availableCategories,
  isLoading = false,
}) => {
  const isEditMode = !!config;

  // Form state
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    model: '',
    provider: 'replicate' as ModelProvider,
    category: '',
    description: '',
    version: '',
    enabled: true,
    tags: [] as string[],
  });

  // JSON field state
  const [replicateSchemaJson, setReplicateSchemaJson] = useState('{}');
  const [customJson, setCustomJson] = useState('{}');
  const [parametersJson, setParametersJson] = useState('{}');

  // Validation state
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Load config data when editing
  useEffect(() => {
    if (config) {
      setFormData({
        id: config.id,
        name: config.name,
        model: config.model,
        provider: config.provider,
        category: config.category,
        description: config.description || '',
        version: config.version || '',
        enabled: config.enabled,
        tags: config.tags || [],
      });
      setReplicateSchemaJson(JSON.stringify(config.replicate_schema || {}, null, 2));
      setCustomJson(JSON.stringify(config.custom || {}, null, 2));
      setParametersJson(JSON.stringify(config.parameters || {}, null, 2));
    } else {
      // Reset form for create mode
      setFormData({
        id: '',
        name: '',
        model: '',
        provider: 'replicate',
        category: availableCategories[0] || '',
        description: '',
        version: '',
        enabled: true,
        tags: [],
      });
      setReplicateSchemaJson('{}');
      setCustomJson('{}');
      setParametersJson('{}');
    }
    setErrors({});
    setGeneralError(null);
  }, [config, availableCategories]);

  // Parse JSON fields
  const parsedJson = useMemo(() => {
    const tryParse = (jsonStr: string, fieldName: string) => {
      try {
        return { value: JSON.parse(jsonStr), error: null };
      } catch (err) {
        return {
          value: null,
          error: err instanceof Error ? err.message : `Invalid JSON in ${fieldName}`,
        };
      }
    };

    return {
      replicateSchema: tryParse(replicateSchemaJson, 'Replicate Schema'),
      custom: tryParse(customJson, 'Custom'),
      parameters: tryParse(parametersJson, 'Parameters'),
    };
  }, [replicateSchemaJson, customJson, parametersJson]);

  // Build preview data
  const previewData = useMemo(() => {
    const data: any = {
      id: formData.id,
      name: formData.name,
      model: formData.model,
      provider: formData.provider,
      category: formData.category,
      description: formData.description,
      enabled: formData.enabled,
      tags: formData.tags,
    };

    if (formData.version) {
      data.version = formData.version;
    }

    if (parsedJson.replicateSchema.value) {
      data.replicate_schema = parsedJson.replicateSchema.value;
    }

    if (parsedJson.custom.value) {
      data.custom = parsedJson.custom.value;
    }

    if (parsedJson.parameters.value) {
      data.parameters = parsedJson.parameters.value;
    }

    return data;
  }, [formData, parsedJson]);

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.id.trim()) {
      newErrors.id = 'ID is required';
    }
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.model.trim()) {
      newErrors.model = 'Model is required';
    }
    if (!formData.category) {
      newErrors.category = 'Category is required';
    }

    // Validate JSON fields
    if (parsedJson.replicateSchema.error) {
      newErrors.replicateSchema = parsedJson.replicateSchema.error;
    }
    if (parsedJson.custom.error) {
      newErrors.custom = parsedJson.custom.error;
    }
    if (parsedJson.parameters.error) {
      newErrors.parameters = parsedJson.parameters.error;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError(null);

    if (!validateForm()) {
      setGeneralError('Please fix the errors before submitting');
      return;
    }

    try {
      const configData: ModelConfigCreate | ModelConfigUpdate = {
        name: formData.name,
        model: formData.model,
        provider: formData.provider,
        category: formData.category,
        description: formData.description || undefined,
        version: formData.version || undefined,
        enabled: formData.enabled,
        tags: formData.tags.length > 0 ? formData.tags : undefined,
        replicate_schema: parsedJson.replicateSchema.value || undefined,
        custom: parsedJson.custom.value || undefined,
        parameters: parsedJson.parameters.value || undefined,
      };

      // For create mode, include ID
      if (!isEditMode) {
        (configData as ModelConfigCreate).id = formData.id;
      }

      await onSave(formData.id, configData);
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save configuration';
      setGeneralError(message);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={isEditMode ? 'Edit Model Configuration' : 'Create Model Configuration'}
      closeOnOverlayClick={!isLoading}
      closeOnEscape={!isLoading}
    >
      <form onSubmit={handleSubmit} className="admin-form model-config-dialog-content">
        {generalError && <ErrorMessage message={generalError} />}

        {/* Basic Information Section */}
        <div className="model-config-section">
          <h3 className="model-config-section-title">Basic Information</h3>

          <div className="model-config-form-row">
            <div className="form-group">
              <label className="form-label">
                ID <span style={{ color: '#c62828' }}>*</span>
              </label>
              <input
                type="text"
                className="form-input"
                value={formData.id}
                onChange={(e) => handleInputChange('id', e.target.value)}
                disabled={isEditMode || isLoading}
                placeholder="e.g., replicate-gfpgan-v1.4"
              />
              {errors.id && <p className="form-help" style={{ color: '#c62828' }}>{errors.id}</p>}
              {!isEditMode && (
                <p className="form-help">Unique identifier. Cannot be changed after creation.</p>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">
                Name <span style={{ color: '#c62828' }}>*</span>
              </label>
              <input
                type="text"
                className="form-input"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                disabled={isLoading}
                placeholder="e.g., GFPGAN Face Restoration"
              />
              {errors.name && <p className="form-help" style={{ color: '#c62828' }}>{errors.name}</p>}
            </div>
          </div>

          <div className="model-config-form-row">
            <div className="form-group">
              <label className="form-label">
                Model <span style={{ color: '#c62828' }}>*</span>
              </label>
              <input
                type="text"
                className="form-input"
                value={formData.model}
                onChange={(e) => handleInputChange('model', e.target.value)}
                disabled={isLoading}
                placeholder="e.g., tencentarc/gfpgan:0fbacf7afc6c144e5be9767cff80f25aff23e52b0708f17e20f9879b2f21516c"
              />
              {errors.model && <p className="form-help" style={{ color: '#c62828' }}>{errors.model}</p>}
              <p className="form-help">Full model identifier (e.g., Replicate model version hash)</p>
            </div>

            <div className="form-group">
              <label className="form-label">Version</label>
              <input
                type="text"
                className="form-input"
                value={formData.version}
                onChange={(e) => handleInputChange('version', e.target.value)}
                disabled={isLoading}
                placeholder="e.g., v1.4"
              />
            </div>
          </div>

          <div className="model-config-form-row">
            <div className="form-group">
              <label className="form-label">
                Provider <span style={{ color: '#c62828' }}>*</span>
              </label>
              <select
                className="form-select"
                value={formData.provider}
                onChange={(e) => handleInputChange('provider', e.target.value as ModelProvider)}
                disabled={isLoading}
              >
                <option value="replicate">Replicate</option>
                <option value="huggingface">Hugging Face</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                Category <span style={{ color: '#c62828' }}>*</span>
              </label>
              <select
                className="form-select"
                value={formData.category}
                onChange={(e) => handleInputChange('category', e.target.value)}
                disabled={isLoading}
              >
                {availableCategories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
              {errors.category && <p className="form-help" style={{ color: '#c62828' }}>{errors.category}</p>}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-textarea"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              disabled={isLoading}
              placeholder="Brief description of what this model does..."
              rows={3}
            />
          </div>

          <div className="form-group checkbox-group">
            <input
              type="checkbox"
              id="enabled"
              className="form-checkbox"
              checked={formData.enabled}
              onChange={(e) => handleInputChange('enabled', e.target.checked)}
              disabled={isLoading}
            />
            <label htmlFor="enabled" className="checkbox-label">
              Enable this model configuration
            </label>
          </div>
        </div>

        {/* Tags Section */}
        <div className="model-config-section">
          <h3 className="model-config-section-title">Tags</h3>
          <TagSelector
            label="Select Tags"
            availableTags={availableTags}
            selectedTags={formData.tags}
            onChange={(tags) => handleInputChange('tags', tags)}
            disabled={isLoading}
          />
        </div>

        {/* JSON Configuration Section */}
        <div className="model-config-section">
          <h3 className="model-config-section-title">JSON Configuration</h3>

          <JsonEditor
            label="Replicate Schema"
            value={replicateSchemaJson}
            onChange={setReplicateSchemaJson}
            placeholder="{}"
            error={errors.replicateSchema}
            disabled={isLoading}
          />

          <JsonEditor
            label="Custom Configuration"
            value={customJson}
            onChange={setCustomJson}
            placeholder="{}"
            error={errors.custom}
            disabled={isLoading}
          />

          <JsonEditor
            label="Parameters"
            value={parametersJson}
            onChange={setParametersJson}
            placeholder="{}"
            error={errors.parameters}
            disabled={isLoading}
          />
        </div>

        {/* Live Preview */}
        <JsonPreview data={previewData} />

        {/* Actions */}
        <div className="modal-actions">
          <Button type="button" variant="secondary" onClick={handleClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={isLoading}>
            {isEditMode ? 'Update Configuration' : 'Create Configuration'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
