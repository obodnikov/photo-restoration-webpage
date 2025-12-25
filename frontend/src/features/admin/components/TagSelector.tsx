/**
 * Tag Selector Component
 * Multi-select checkboxes for model tags
 */

import React from 'react';

export interface TagSelectorProps {
  label: string;
  availableTags: string[];
  selectedTags: string[];
  onChange: (tags: string[]) => void;
  disabled?: boolean;
}

export const TagSelector: React.FC<TagSelectorProps> = ({
  label,
  availableTags,
  selectedTags,
  onChange,
  disabled = false,
}) => {
  const handleToggle = (tag: string) => {
    if (disabled) return;

    if (selectedTags.includes(tag)) {
      onChange(selectedTags.filter((t) => t !== tag));
    } else {
      onChange([...selectedTags, tag]);
    }
  };

  return (
    <div className="tag-selector-container">
      <label className="form-label">{label}</label>
      <div className="tag-selector-grid">
        {availableTags.map((tag) => (
          <div key={tag} className="tag-checkbox-item">
            <input
              type="checkbox"
              id={`tag-${tag}`}
              checked={selectedTags.includes(tag)}
              onChange={() => handleToggle(tag)}
              disabled={disabled}
            />
            <label htmlFor={`tag-${tag}`} className="tag-checkbox-label">
              {tag}
            </label>
          </div>
        ))}
      </div>
    </div>
  );
};
