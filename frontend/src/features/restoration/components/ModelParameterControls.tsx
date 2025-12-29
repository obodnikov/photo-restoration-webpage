/**
 * Container for all parameter inputs for a model
 */
import React, { useMemo } from 'react';
import type { ModelInfo, ModelParameterValues } from '../types';
import { ParameterInput } from './parameter-inputs/ParameterInput';
import { getParameterUIConfig } from '../utils/parameterUtils';
import './ModelParameterControls.css';

export interface ModelParameterControlsProps {
  model: ModelInfo;
  values: ModelParameterValues;
  onChange: (values: ModelParameterValues) => void;
  disabled?: boolean;
}

export const ModelParameterControls: React.FC<ModelParameterControlsProps> = ({
  model,
  values,
  onChange,
  disabled = false,
}) => {
  // Filter and sort visible parameters with error handling
  const visibleParams = useMemo(() => {
    // Validate model structure
    if (!model) {
      console.warn('[ModelParameterControls] Model is null or undefined');
      return [];
    }

    if (!model.schema) {
      // No schema is valid - means no parameters to configure
      return [];
    }

    if (!Array.isArray(model.schema.parameters)) {
      console.error(
        '[ModelParameterControls] Invalid schema.parameters:',
        model.schema.parameters
      );
      return [];
    }

    try {
      return model.schema.parameters
        .map((param) => {
          // Validate parameter structure
          if (!param || typeof param !== 'object' || !param.name) {
            console.warn('[ModelParameterControls] Invalid parameter:', param);
            return null;
          }

          try {
            const uiConfig = getParameterUIConfig(param.name, param, model);
            return { param, uiConfig };
          } catch (error) {
            console.error(
              `[ModelParameterControls] Error getting UI config for parameter "${param.name}":`,
              error
            );
            return null;
          }
        })
        .filter(
          (item): item is { param: any; uiConfig: any } =>
            item !== null && item.uiConfig !== null
        )
        .sort((a, b) => {
          const orderA = a.uiConfig?.order ?? 999;
          const orderB = b.uiConfig?.order ?? 999;
          return orderA - orderB;
        });
    } catch (error) {
      console.error('[ModelParameterControls] Error processing parameters:', error);
      return [];
    }
  }, [model]);

  if (visibleParams.length === 0) {
    return null;
  }

  const handleChange = (paramName: string, value: any) => {
    onChange({
      ...values,
      [paramName]: value,
    });
  };

  return (
    <div className="model-parameter-controls">
      <div className="parameter-controls-header">
        <h4>Parameters</h4>
        <span className="parameter-count">{visibleParams.length}</span>
      </div>
      <div className="parameter-controls-list">
        {visibleParams.map(({ param, uiConfig }) => (
          <div key={param.name} className="parameter-control-item">
            <ParameterInput
              param={param}
              uiConfig={uiConfig!}
              value={values[param.name] ?? param.default}
              onChange={(value) => handleChange(param.name, value)}
              disabled={disabled}
            />
          </div>
        ))}
      </div>
    </div>
  );
};
