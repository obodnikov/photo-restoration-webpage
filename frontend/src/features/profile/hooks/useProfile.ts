/**
 * useProfile hook - manages user profile data and operations
 */

import { useState, useEffect, useCallback } from 'react';
import { profileService } from '../services/profileService';
import type { UserProfile, Session } from '../types';

export function useProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch user profile
   */
  const fetchProfile = useCallback(async () => {
    setIsLoadingProfile(true);
    setError(null);

    try {
      const data = await profileService.getProfile();
      setProfile(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load profile';
      setError(message);
      console.error('Error fetching profile:', err);
    } finally {
      setIsLoadingProfile(false);
    }
  }, []);

  /**
   * Fetch active sessions
   */
  const fetchSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    setError(null);

    try {
      const data = await profileService.getSessions();
      setSessions(data.sessions);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load sessions';
      setError(message);
      console.error('Error fetching sessions:', err);
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  /**
   * Change password
   */
  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      setIsChangingPassword(true);
      setError(null);

      try {
        await profileService.changePassword({
          current_password: currentPassword,
          new_password: newPassword,
        });

        // Refresh profile to clear password_must_change flag if it was set
        await fetchProfile();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to change password';
        setError(message);
        throw err; // Re-throw so the form can handle it
      } finally {
        setIsChangingPassword(false);
      }
    },
    [fetchProfile]
  );

  /**
   * Delete a session (remote logout)
   */
  const deleteSession = useCallback(async (sessionId: string) => {
    setError(null);

    try {
      await profileService.deleteSession(sessionId);

      // Remove the session from local state
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete session';
      setError(message);
      throw err; // Re-throw so the component can handle it
    }
  }, []);

  /**
   * Load initial data on mount
   */
  useEffect(() => {
    void fetchProfile();
    void fetchSessions();
  }, [fetchProfile, fetchSessions]);

  return {
    profile,
    sessions,
    isLoadingProfile,
    isLoadingSessions,
    isChangingPassword,
    error,
    changePassword,
    deleteSession,
    refreshProfile: fetchProfile,
    refreshSessions: fetchSessions,
  };
}
