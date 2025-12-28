/**
 * JSON Preview Component
 * Displays live preview of JSON with validation and copy-to-clipboard
 */

import React, { useState, useMemo } from 'react';
import { Button } from '../../../components/Button';

export interface JsonPreviewProps {
  data: Record<string, any>;
}

export const JsonPreview: React.FC<JsonPreviewProps> = ({ data }) => {
  const [copied, setCopied] = useState(false);

  const { jsonString, isValid, error } = useMemo(() => {
    try {
      const json = JSON.stringify(data, null, 2);
      return { jsonString: json, isValid: true, error: null };
    } catch (err) {
      return {
        jsonString: '',
        isValid: false,
        error: err instanceof Error ? err.message : 'Invalid JSON',
      };
    }
  }, [data]);

  const handleCopy = async () => {
    if (!isValid) return;

    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  return (
    <div className="json-preview-container">
      <div className="json-preview-header">
        <div className="json-preview-title">
          Live Preview
        </div>
        <div className="json-preview-status-actions">
          <div className={`json-preview-status ${isValid ? 'valid' : 'invalid'}`}>
            {isValid ? (
              <>
                <span>✓</span>
                <span>Valid JSON</span>
              </>
            ) : (
              <>
                <span>✗</span>
                <span>Invalid JSON</span>
              </>
            )}
          </div>
          {isValid && (
            <Button
              type="button"
              variant="secondary"
              size="small"
              onClick={handleCopy}
            >
              {copied ? 'Copied!' : 'Copy'}
            </Button>
          )}
        </div>
      </div>

      {isValid ? (
        <div className="json-preview-code">
          <pre>{jsonString}</pre>
        </div>
      ) : (
        <div className="json-error-message">
          {error}
        </div>
      )}
    </div>
  );
};
