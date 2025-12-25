/**
 * Admin feature types
 */

/**
 * User from admin API
 */
export interface AdminUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

/**
 * Create user request
 */
export interface CreateUserRequest {
  username: string;
  email: string;
  full_name: string;
  password: string;
  role: 'admin' | 'user';
  password_must_change: boolean;
}

/**
 * Update user request
 */
export interface UpdateUserRequest {
  email?: string;
  full_name?: string;
  role?: 'admin' | 'user';
  is_active?: boolean;
}

/**
 * Reset password request
 */
export interface ResetPasswordRequest {
  new_password: string;
  password_must_change: boolean;
}

/**
 * User list response
 */
export interface UserListResponse {
  users: AdminUser[];
  total: number;
}

/**
 * User list filters
 */
export interface UserListFilters {
  role?: 'admin' | 'user' | null;
  is_active?: boolean | null;
}

// ===== Model Configuration Types =====

/**
 * Model configuration source
 */
export type ModelConfigSource = 'local' | 'production' | 'development' | 'testing' | 'default';

/**
 * Provider types
 */
export type ModelProvider = 'huggingface' | 'replicate';

/**
 * Model configuration list item
 */
export interface ModelConfigListItem {
  id: string;
  name: string;
  provider: ModelProvider;
  category: string;
  enabled: boolean;
  source: ModelConfigSource;
  tags: string[];
  version?: string;
}

/**
 * Full model configuration
 */
export interface ModelConfigDetail {
  id: string;
  name: string;
  model: string;
  provider: ModelProvider;
  category: string;
  description: string;
  enabled: boolean;
  tags: string[];
  version?: string;
  replicate_schema?: Record<string, any>;
  custom?: Record<string, any>;
  parameters: Record<string, any>;
  source: ModelConfigSource;
}

/**
 * Create model config request
 */
export interface ModelConfigCreate {
  id: string;
  name: string;
  model: string;
  provider: ModelProvider;
  category: string;
  description?: string;
  enabled?: boolean;
  tags?: string[];
  version?: string;
  replicate_schema?: Record<string, any>;
  custom?: Record<string, any>;
  parameters?: Record<string, any>;
}

/**
 * Update model config request
 */
export interface ModelConfigUpdate {
  name?: string;
  model?: string;
  provider?: ModelProvider;
  category?: string;
  description?: string;
  enabled?: boolean;
  tags?: string[];
  version?: string;
  replicate_schema?: Record<string, any>;
  custom?: Record<string, any>;
  parameters?: Record<string, any>;
}

/**
 * Available tags and categories
 */
export interface AvailableTagsResponse {
  tags: string[];
  categories: string[];
}

/**
 * Validation error
 */
export interface ValidationError {
  field: string;
  message: string;
}

/**
 * Validation response
 */
export interface ModelConfigValidationResponse {
  valid: boolean;
  errors: ValidationError[];
}
