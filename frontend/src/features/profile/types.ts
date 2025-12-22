/**
 * Types for user profile feature
 */

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'user';
  is_active: boolean;
  password_must_change: boolean;
  created_at: string;
  last_login: string | null;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface Session {
  id: string;
  created_at: string;
  last_accessed: string;
  is_current: boolean;
}

export interface SessionsResponse {
  sessions: Session[];
  total: number;
}
