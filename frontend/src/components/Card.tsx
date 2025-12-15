/**
 * Card component with sqowe brand styling
 * Supports light and dark variants
 */

import React from 'react';

export interface CardProps {
  title?: string;
  description?: string;
  variant?: 'light' | 'dark';
  className?: string;
  children?: React.ReactNode;
  onClick?: () => void;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  title,
  description,
  variant = 'light',
  className = '',
  children,
  onClick,
  hoverable = false,
}) => {
  const baseClass = 'card';
  const variantClass = `card-${variant}`;
  const hoverableClass = hoverable || onClick ? 'card-hoverable' : '';
  const clickableClass = onClick ? 'card-clickable' : '';

  const classes = [baseClass, variantClass, hoverableClass, clickableClass, className]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes} onClick={onClick}>
      {title && (
        <div className="card-header">
          <h3 className="card-title">{title}</h3>
        </div>
      )}
      {description && <p className="card-description">{description}</p>}
      {children && <div className="card-content">{children}</div>}
    </div>
  );
};
