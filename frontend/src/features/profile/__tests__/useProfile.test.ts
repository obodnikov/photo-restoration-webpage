import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useProfile } from '../hooks/useProfile';
import { profileService } from '../services/profileService';
import type { UserProfile, Session } from '../types';

// Mock the profile service
vi.mock('../services/profileService', () => ({
  profileService: {
    getProfile: vi.fn(),
    getSessions: vi.fn(),
    changePassword: vi.fn(),
    deleteSession: vi.fn(),
  },
}));

describe('useProfile', () => {
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

  const mockSessions: Session[] = [
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
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(profileService.getProfile).mockResolvedValue(mockProfile);
    vi.mocked(profileService.getSessions).mockResolvedValue({
      sessions: mockSessions,
      total: mockSessions.length,
    });
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Initial State', () => {
    it('initializes with correct default state', () => {
      const { result } = renderHook(() => useProfile());

      expect(result.current.profile).toBeNull();
      expect(result.current.sessions).toEqual([]);
      expect(result.current.isLoadingProfile).toBe(false);
      expect(result.current.isLoadingSessions).toBe(false);
      expect(result.current.isChangingPassword).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Fetch Profile', () => {
    it('fetches profile on mount', async () => {
      renderHook(() => useProfile());

      await waitFor(() => {
        expect(profileService.getProfile).toHaveBeenCalledTimes(1);
      });
    });

    it('sets loading state while fetching profile', async () => {
      let resolveProfile: (value: UserProfile) => void;
      const profilePromise = new Promise<UserProfile>((resolve) => {
        resolveProfile = resolve;
      });
      vi.mocked(profileService.getProfile).mockReturnValue(profilePromise);

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.isLoadingProfile).toBe(true);
      });

      resolveProfile!(mockProfile);

      await waitFor(() => {
        expect(result.current.isLoadingProfile).toBe(false);
      });
    });

    it('updates profile state on successful fetch', async () => {
      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.profile).toEqual(mockProfile);
      });
    });

    it('sets error on profile fetch failure', async () => {
      vi.mocked(profileService.getProfile).mockRejectedValue(new Error('Failed to load'));

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to load');
        expect(result.current.profile).toBeNull();
      });
    });

    it('handles non-Error exceptions during profile fetch', async () => {
      vi.mocked(profileService.getProfile).mockRejectedValue('String error');

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to load profile');
      });
    });
  });

  describe('Fetch Sessions', () => {
    it('fetches sessions on mount', async () => {
      renderHook(() => useProfile());

      await waitFor(() => {
        expect(profileService.getSessions).toHaveBeenCalledTimes(1);
      });
    });

    it('sets loading state while fetching sessions', async () => {
      let resolveSessions: (value: { sessions: Session[]; total: number }) => void;
      const sessionsPromise = new Promise<{ sessions: Session[]; total: number }>((resolve) => {
        resolveSessions = resolve;
      });
      vi.mocked(profileService.getSessions).mockReturnValue(sessionsPromise);

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.isLoadingSessions).toBe(true);
      });

      resolveSessions!({ sessions: mockSessions, total: mockSessions.length });

      await waitFor(() => {
        expect(result.current.isLoadingSessions).toBe(false);
      });
    });

    it('updates sessions state on successful fetch', async () => {
      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.sessions).toEqual(mockSessions);
      });
    });

    it('sets error on sessions fetch failure', async () => {
      vi.mocked(profileService.getSessions).mockRejectedValue(new Error('Sessions error'));

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.error).toBe('Sessions error');
        expect(result.current.sessions).toEqual([]);
      });
    });
  });

  describe('Change Password', () => {
    it('calls profileService.changePassword with correct arguments', async () => {
      vi.mocked(profileService.changePassword).mockResolvedValue({ message: 'Success' });

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.profile).not.toBeNull();
      });

      await result.current.changePassword('oldPass123', 'newPass456');

      expect(profileService.changePassword).toHaveBeenCalledWith({
        current_password: 'oldPass123',
        new_password: 'newPass456',
      });
    });

    it('sets loading state during password change', async () => {
      let resolvePasswordChange: (value: { message: string }) => void;
      const passwordPromise = new Promise<{ message: string }>((resolve) => {
        resolvePasswordChange = resolve;
      });
      vi.mocked(profileService.changePassword).mockReturnValue(passwordPromise);

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.profile).not.toBeNull();
      });

      const changePromise = result.current.changePassword('oldPass123', 'newPass456');

      await waitFor(() => {
        expect(result.current.isChangingPassword).toBe(true);
      });

      resolvePasswordChange!({ message: 'Success' });
      await changePromise;

      await waitFor(() => {
        expect(result.current.isChangingPassword).toBe(false);
      });
    });

    it('refreshes profile after successful password change', async () => {
      vi.mocked(profileService.changePassword).mockResolvedValue({ message: 'Success' });

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.profile).not.toBeNull();
      });

      // Clear the mock call count
      vi.mocked(profileService.getProfile).mockClear();

      await result.current.changePassword('oldPass123', 'newPass456');

      await waitFor(() => {
        // Should be called once for refresh
        expect(profileService.getProfile).toHaveBeenCalledTimes(1);
      });
    });

    it('throws error on password change failure', async () => {
      const error = new Error('Wrong password');
      vi.mocked(profileService.changePassword).mockRejectedValue(error);

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.profile).not.toBeNull();
      });

      await expect(result.current.changePassword('wrong', 'new')).rejects.toThrow('Wrong password');
    });

    it('sets error state on password change failure', async () => {
      vi.mocked(profileService.changePassword).mockRejectedValue(new Error('Wrong password'));

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.profile).not.toBeNull();
      });

      try {
        await result.current.changePassword('wrong', 'new');
      } catch {
        // Expected to throw
      }

      await waitFor(() => {
        expect(result.current.error).toBe('Wrong password');
      });
    });

    it('handles non-Error exceptions during password change', async () => {
      vi.mocked(profileService.changePassword).mockRejectedValue('String error');

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.profile).not.toBeNull();
      });

      try {
        await result.current.changePassword('old', 'new');
      } catch {
        // Expected to throw
      }

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to change password');
      });
    });
  });

  describe('Delete Session', () => {
    it('calls profileService.deleteSession with correct session ID', async () => {
      vi.mocked(profileService.deleteSession).mockResolvedValue({ message: 'Deleted' });

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.sessions).toEqual(mockSessions);
      });

      await result.current.deleteSession('session-2');

      expect(profileService.deleteSession).toHaveBeenCalledWith('session-2');
    });

    it('removes session from local state after successful deletion', async () => {
      vi.mocked(profileService.deleteSession).mockResolvedValue({ message: 'Deleted' });

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.sessions).toEqual(mockSessions);
      });

      await result.current.deleteSession('session-2');

      await waitFor(() => {
        expect(result.current.sessions).toHaveLength(1);
        expect(result.current.sessions[0].id).toBe('session-1');
      });
    });

    it('throws error on session deletion failure', async () => {
      const error = new Error('Deletion failed');
      vi.mocked(profileService.deleteSession).mockRejectedValue(error);

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.sessions).toEqual(mockSessions);
      });

      await expect(result.current.deleteSession('session-2')).rejects.toThrow('Deletion failed');
    });

    it('sets error state on session deletion failure', async () => {
      vi.mocked(profileService.deleteSession).mockRejectedValue(new Error('Deletion failed'));

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.sessions).toEqual(mockSessions);
      });

      try {
        await result.current.deleteSession('session-2');
      } catch {
        // Expected to throw
      }

      await waitFor(() => {
        expect(result.current.error).toBe('Deletion failed');
      });
    });

    it('handles non-Error exceptions during session deletion', async () => {
      vi.mocked(profileService.deleteSession).mockRejectedValue('String error');

      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.sessions).toEqual(mockSessions);
      });

      try {
        await result.current.deleteSession('session-2');
      } catch {
        // Expected to throw
      }

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to delete session');
      });
    });
  });

  describe('Manual Refresh', () => {
    it('provides refreshProfile function', async () => {
      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.profile).not.toBeNull();
      });

      expect(typeof result.current.refreshProfile).toBe('function');
    });

    it('refreshProfile fetches profile again', async () => {
      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.profile).not.toBeNull();
      });

      // Clear the initial call
      vi.mocked(profileService.getProfile).mockClear();

      await result.current.refreshProfile();

      await waitFor(() => {
        expect(profileService.getProfile).toHaveBeenCalledTimes(1);
      });
    });

    it('provides refreshSessions function', async () => {
      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.sessions).toEqual(mockSessions);
      });

      expect(typeof result.current.refreshSessions).toBe('function');
    });

    it('refreshSessions fetches sessions again', async () => {
      const { result } = renderHook(() => useProfile());

      await waitFor(() => {
        expect(result.current.sessions).toEqual(mockSessions);
      });

      // Clear the initial call
      vi.mocked(profileService.getSessions).mockClear();

      await result.current.refreshSessions();

      await waitFor(() => {
        expect(profileService.getSessions).toHaveBeenCalledTimes(1);
      });
    });
  });
});
