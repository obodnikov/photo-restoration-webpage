/**
 * Profile service for user profile API calls
 */

import * as api from '../../../services/apiClient';
import type { UserProfile, ChangePasswordRequest, SessionsResponse } from '../types';

export const profileService = {
  /**
   * Get current user profile
   */
  async getProfile(): Promise<UserProfile> {
    return api.get<UserProfile>('/users/me');
  },

  /**
   * Change user password
   */
  async changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
    return api.put<{ message: string }>('/users/me/password', data);
  },

  /**
   * Get active sessions for current user
   */
  async getSessions(): Promise<SessionsResponse> {
    return api.get<SessionsResponse>('/users/me/sessions');
  },

  /**
   * Delete a specific session (remote logout)
   */
  async deleteSession(sessionId: string): Promise<void> {
    return api.del<void>(`/users/me/sessions/${sessionId}`);
  },
};
