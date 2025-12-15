/**
 * Loader component with sqowe brand styling
 * Displays a loading spinner with optional text
 */

import React from 'react';

export interface LoaderProps {
  text?: string;
  size?: 'small' | 'medium' | 'large';
  fullScreen?: boolean;
  className?: string;
}

export const Loader: React.FC<LoaderProps> = ({
  text,
  size = 'medium',
  fullScreen = false,
  className = '',
}) => {
  const containerClass = fullScreen ? 'loader-container loader-fullscreen' : 'loader-container';
  const spinnerClass = `loader-spinner loader-${size}`;

  return (
    <div className={`${containerClass} ${className}`}>
      <div className={spinnerClass}></div>
      {text && <p className="loader-text">{text}</p>}
    </div>
  );
};
