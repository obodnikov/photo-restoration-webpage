/**
 * ModelSelector component
 * Displays available models and allows selection
 */

import React, { useEffect, useState } from 'react';
import { fetchModels } from '../services/restorationService';
import type { ModelInfo } from '../types';
import { Loader } from '../../../components/Loader';
import { ErrorMessage } from '../../../components/ErrorMessage';

export interface ModelSelectorProps {
  selectedModel: ModelInfo | null;
  onSelectModel: (model: ModelInfo) => void;
  disabled?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModel,
  onSelectModel,
  disabled = false,
}) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetchModels();
      setModels(response.models);

      // Auto-select first model if none selected
      if (!selectedModel && response.models.length > 0) {
        onSelectModel(response.models[0]);
      }
    } catch (err) {
      setError('Failed to load models. Please try again.');
      console.error('Error loading models:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <Loader text="Loading models..." size="medium" />;
  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        title="Model Loading Error"
        onClose={() => loadModels()}
      />
    );
  }

  if (models.length === 0) {
    return (
      <div className="model-selector-empty">
        <p>No models available</p>
      </div>
    );
  }

  return (
    <div className="model-selector">
      <label className="model-selector-label">
        Select AI Model
      </label>
      <div className="model-selector-grid">
        {models.map((model) => (
          <button
            key={model.id}
            type="button"
            className={`model-card ${
              selectedModel?.id === model.id ? 'selected' : ''
            }`}
            onClick={() => onSelectModel(model)}
            disabled={disabled}
          >
            <div className="model-card-header">
              <h4 className="model-card-title">{model.name}</h4>
              {model.category && (
                <span className="model-card-category">{model.category}</span>
              )}
            </div>
            <p className="model-card-description">{model.description}</p>
            {model.tags && model.tags.length > 0 && (
              <div className="model-card-tags">
                {model.tags.map((tag) => (
                  <span key={tag} className="model-tag">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};
