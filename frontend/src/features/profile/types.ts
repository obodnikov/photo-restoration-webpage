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
  id: number;
  session_id: string;
  created_at: string;
  last_accessed: string;
  is_current: boolean;
  user_agent?: string | null;
  ip_address?: string | null;
  device_type?: string | null;
  browser?: string | null;
  os?: string | null;
  location?: string | null;
}

export interface SessionsResponse {
  sessions: Session[];
  total: number;
}
