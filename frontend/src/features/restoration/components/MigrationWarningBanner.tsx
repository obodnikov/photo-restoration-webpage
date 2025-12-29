/**
 * MigrationWarningBanner - Warning banner for UI parameter migration
 *
 * Displays when models need migration to support Custom Model Parameters UI feature
 */

import React, { useEffect, useState } from 'react';
import './MigrationWarningBanner.css';

interface MigrationStatus {
  needs_migration: boolean;
  count: number;
  model_ids: string[];
  missing_params: string[];
  migration_command: string;
}

export const MigrationWarningBanner: React.FC = () => {
  const [migrationStatus, setMigrationStatus] = useState<MigrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const checkMigrationStatus = async () => {
      try {
        const response = await fetch('/api/v1/models/migration/status');
        if (!response.ok) {
          console.error('Failed to fetch migration status');
          setLoading(false);
          return;
        }

        const data: MigrationStatus = await response.json();
        setMigrationStatus(data);
      } catch (error) {
        console.error('Error checking migration status:', error);
      } finally {
        setLoading(false);
      }
    };

    // Check if user has dismissed the warning in this session
    const wasDismissed = sessionStorage.getItem('migration_warning_dismissed') === 'true';
    setDismissed(wasDismissed);

    if (!wasDismissed) {
      checkMigrationStatus();
    } else {
      setLoading(false);
    }
  }, []);

  const handleDismiss = () => {
    setDismissed(true);
    sessionStorage.setItem('migration_warning_dismissed', 'true');
  };

  // Don't render if loading, dismissed, or no migration needed
  if (loading || dismissed || !migrationStatus || !migrationStatus.needs_migration) {
    return null;
  }

  return (
    <div className="migration-warning-banner" role="alert">
      <div className="migration-warning-content">
        <div className="migration-warning-icon">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>

        <div className="migration-warning-text">
          <h3 className="migration-warning-title">⚠️ Configuration Migration Required</h3>
          <p className="migration-warning-message">
            {migrationStatus.count} model{migrationStatus.count > 1 ? 's' : ''} need migration to support
            the new Custom Model Parameters UI feature.
          </p>
          <details className="migration-warning-details">
            <summary>Show details</summary>
            <div className="migration-details-content">
              <p><strong>Models requiring migration:</strong></p>
              <ul>
                {migrationStatus.model_ids.map((modelId) => (
                  <li key={modelId}>{modelId}</li>
                ))}
              </ul>
              <p><strong>Migration command:</strong></p>
              <code className="migration-command">{migrationStatus.migration_command}</code>
              <p className="migration-help-text">
                Run this command from the project root directory to automatically migrate your configuration files.
                See the README.md "Breaking Changes" section for more information.
              </p>
            </div>
          </details>
        </div>

        <button
          className="migration-warning-dismiss"
          onClick={handleDismiss}
          aria-label="Dismiss warning"
          title="Dismiss for this session"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
  );
};
