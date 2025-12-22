import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { profileService } from '../services/profileService';
import * as api from '../../../services/apiClient';
import type { UserProfile, SessionsResponse } from '../types';

// Mock the API client
vi.mock('../../../services/apiClient', () => ({
  get: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}));

describe('profileService', () => {
  const mockProfile: UserProfile = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    full_name: 'Test User',
    role: 'user',
    is_active: true,
    password_must_change: false,
    created_at: '2024-01-01T00:00:00Z',
    last_login: '2024-12-22T10:00:00Z',
  };

  const mockSessionsResponse: SessionsResponse = {
    sessions: [
      {
        id: 'session-1',
        created_at: '2024-12-20T10:00:00Z',
        last_accessed: '2024-12-22T10:00:00Z',
        is_current: true,
      },
      {
        id: 'session-2',
        created_at: '2024-12-19T14:00:00Z',
        last_accessed: '2024-12-21T16:00:00Z',
        is_current: false,
      },
    ],
    total: 2,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('getProfile', () => {
    it('calls api.get with correct endpoint', async () => {
      vi.mocked(api.get).mockResolvedValue(mockProfile);

      await profileService.getProfile();

      expect(api.get).toHaveBeenCalledWith('/users/me');
    });

    it('returns user profile on success', async () => {
      vi.mocked(api.get).mockResolvedValue(mockProfile);

      const result = await profileService.getProfile();

      expect(result).toEqual(mockProfile);
    });

    it('throws error on API failure', async () => {
      const error = new Error('API Error');
      vi.mocked(api.get).mockRejectedValue(error);

      await expect(profileService.getProfile()).rejects.toThrow('API Error');
    });

    it('handles 401 unauthorized errors', async () => {
      const error = new Error('401: Unauthorized');
      vi.mocked(api.get).mockRejectedValue(error);

      await expect(profileService.getProfile()).rejects.toThrow('401: Unauthorized');
    });

    it('handles 404 not found errors', async () => {
      const error = new Error('404: Not Found');
      vi.mocked(api.get).mockRejectedValue(error);

      await expect(profileService.getProfile()).rejects.toThrow('404: Not Found');
    });

    it('handles network errors', async () => {
      const error = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(error);

      await expect(profileService.getProfile()).rejects.toThrow('Network error');
    });
  });

  describe('changePassword', () => {
    const passwordData = {
      current_password: 'oldPass123',
      new_password: 'newPass456',
    };

    it('calls api.put with correct endpoint and data', async () => {
      vi.mocked(api.put).mockResolvedValue({ message: 'Password changed' });

      await profileService.changePassword(passwordData);

      expect(api.put).toHaveBeenCalledWith('/users/me/password', passwordData);
    });

    it('returns success message on password change', async () => {
      const response = { message: 'Password changed successfully' };
      vi.mocked(api.put).mockResolvedValue(response);

      const result = await profileService.changePassword(passwordData);

      expect(result).toEqual(response);
    });

    it('throws error on API failure', async () => {
      const error = new Error('API Error');
      vi.mocked(api.put).mockRejectedValue(error);

      await expect(profileService.changePassword(passwordData)).rejects.toThrow('API Error');
    });

    it('handles incorrect current password error', async () => {
      const error = new Error('401: Current password is incorrect');
      vi.mocked(api.put).mockRejectedValue(error);

      await expect(profileService.changePassword(passwordData)).rejects.toThrow(
        '401: Current password is incorrect'
      );
    });

    it('handles password validation errors', async () => {
      const error = new Error('400: Password does not meet requirements');
      vi.mocked(api.put).mockRejectedValue(error);

      await expect(profileService.changePassword(passwordData)).rejects.toThrow(
        '400: Password does not meet requirements'
      );
    });

    it('handles weak password errors', async () => {
      const error = new Error('Password is too weak');
      vi.mocked(api.put).mockRejectedValue(error);

      await expect(profileService.changePassword(passwordData)).rejects.toThrow(
        'Password is too weak'
      );
    });
  });

  describe('getSessions', () => {
    it('calls api.get with correct endpoint', async () => {
      vi.mocked(api.get).mockResolvedValue(mockSessionsResponse);

      await profileService.getSessions();

      expect(api.get).toHaveBeenCalledWith('/users/me/sessions');
    });

    it('returns sessions list on success', async () => {
      vi.mocked(api.get).mockResolvedValue(mockSessionsResponse);

      const result = await profileService.getSessions();

      expect(result).toEqual(mockSessionsResponse);
      expect(result.sessions).toHaveLength(2);
      expect(result.total).toBe(2);
    });

    it('handles empty sessions list', async () => {
      const emptyResponse: SessionsResponse = { sessions: [], total: 0 };
      vi.mocked(api.get).mockResolvedValue(emptyResponse);

      const result = await profileService.getSessions();

      expect(result.sessions).toEqual([]);
      expect(result.total).toBe(0);
    });

    it('throws error on API failure', async () => {
      const error = new Error('API Error');
      vi.mocked(api.get).mockRejectedValue(error);

      await expect(profileService.getSessions()).rejects.toThrow('API Error');
    });

    it('handles unauthorized errors', async () => {
      const error = new Error('401: Unauthorized');
      vi.mocked(api.get).mockRejectedValue(error);

      await expect(profileService.getSessions()).rejects.toThrow('401: Unauthorized');
    });
  });

  describe('deleteSession', () => {
    const sessionId = 'session-123';

    it('calls api.del with correct endpoint', async () => {
      vi.mocked(api.del).mockResolvedValue({ message: 'Session deleted' });

      await profileService.deleteSession(sessionId);

      expect(api.del).toHaveBeenCalledWith(`/users/me/sessions/${sessionId}`);
    });

    it('returns success message on session deletion', async () => {
      const response = { message: 'Session deleted successfully' };
      vi.mocked(api.del).mockResolvedValue(response);

      const result = await profileService.deleteSession(sessionId);

      expect(result).toEqual(response);
    });

    it('handles deleting current session', async () => {
      vi.mocked(api.del).mockResolvedValue({ message: 'Current session deleted' });

      const result = await profileService.deleteSession('current-session');

      expect(result.message).toBeTruthy();
    });

    it('throws error on API failure', async () => {
      const error = new Error('API Error');
      vi.mocked(api.del).mockRejectedValue(error);

      await expect(profileService.deleteSession(sessionId)).rejects.toThrow('API Error');
    });

    it('handles session not found error', async () => {
      const error = new Error('404: Session not found');
      vi.mocked(api.del).mockRejectedValue(error);

      await expect(profileService.deleteSession(sessionId)).rejects.toThrow(
        '404: Session not found'
      );
    });

    it('handles forbidden deletion error', async () => {
      const error = new Error('403: Cannot delete this session');
      vi.mocked(api.del).mockRejectedValue(error);

      await expect(profileService.deleteSession(sessionId)).rejects.toThrow(
        '403: Cannot delete this session'
      );
    });

    it('handles unauthorized errors', async () => {
      const error = new Error('401: Unauthorized');
      vi.mocked(api.del).mockRejectedValue(error);

      await expect(profileService.deleteSession(sessionId)).rejects.toThrow('401: Unauthorized');
    });
  });

  describe('API Integration', () => {
    it('all methods use proper HTTP verbs', async () => {
      vi.mocked(api.get).mockResolvedValue(mockProfile);
      vi.mocked(api.put).mockResolvedValue({ message: 'Success' });
      vi.mocked(api.del).mockResolvedValue({ message: 'Deleted' });

      await profileService.getProfile();
      expect(api.get).toHaveBeenCalled();

      await profileService.getSessions();
      expect(api.get).toHaveBeenCalled();

      await profileService.changePassword({
        current_password: 'old',
        new_password: 'new',
      });
      expect(api.put).toHaveBeenCalled();

      await profileService.deleteSession('session-1');
      expect(api.del).toHaveBeenCalled();
    });

    it('handles concurrent API calls', async () => {
      vi.mocked(api.get).mockResolvedValue(mockProfile);
      vi.mocked(api.get).mockResolvedValue(mockSessionsResponse);

      const [profile, sessions] = await Promise.all([
        profileService.getProfile(),
        profileService.getSessions(),
      ]);

      expect(profile).toBeDefined();
      expect(sessions).toBeDefined();
    });

    it('properly propagates TypeScript types', async () => {
      vi.mocked(api.get).mockResolvedValue(mockProfile);

      const profile = await profileService.getProfile();

      // TypeScript should ensure these properties exist
      expect(profile.username).toBe(mockProfile.username);
      expect(profile.email).toBe(mockProfile.email);
      expect(profile.role).toBe(mockProfile.role);
      expect(profile.is_active).toBe(mockProfile.is_active);
    });
  });

  describe('Error Handling', () => {
    it('preserves error details from API client', async () => {
      const originalError = new Error('Detailed API error message');
      vi.mocked(api.get).mockRejectedValue(originalError);

      try {
        await profileService.getProfile();
        expect.fail('Should have thrown error');
      } catch (error) {
        expect(error).toBe(originalError);
        expect((error as Error).message).toBe('Detailed API error message');
      }
    });

    it('handles malformed API responses gracefully', async () => {
      vi.mocked(api.get).mockResolvedValue(null);

      const result = await profileService.getProfile();
      expect(result).toBeNull();
    });
  });
});
