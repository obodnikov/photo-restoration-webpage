/**
 * ProfilePage component tests
 * Tests the error handling logic and component rendering
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProfilePage } from '../pages/ProfilePage';
import { useProfile } from '../hooks/useProfile';
import type { UserProfile, Session } from '../types';

// Mock the useProfile hook
vi.mock('../hooks/useProfile');

describe('ProfilePage', () => {
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
      user_id: 1,
      device: 'Chrome on Windows',
      ip_address: '192.168.1.1',
      created_at: '2024-12-22T10:00:00Z',
      last_active: '2024-12-22T11:00:00Z',
      is_current: true,
    },
  ];

  const defaultHookReturn = {
    profile: mockProfile,
    sessions: mockSessions,
    isLoadingProfile: false,
    isLoadingSessions: false,
    isChangingPassword: false,
    profileError: null,
    sessionsError: null,
    mutationError: null,
    changePassword: vi.fn(),
    deleteSession: vi.fn(),
    refreshProfile: vi.fn(),
    refreshSessions: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading States', () => {
    it('shows loader during initial profile load', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: null,
        isLoadingProfile: true,
        profileError: null,
      });

      render(<ProfilePage />);

      expect(screen.getByText(/loading profile/i)).toBeInTheDocument();
    });

    it('does not show loader when profile exists and is refreshing', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: mockProfile,
        isLoadingProfile: true,
      });

      render(<ProfilePage />);

      // Should show profile content, not loader
      expect(screen.queryByText(/loading profile/i)).not.toBeInTheDocument();
      expect(screen.getByText('My Profile')).toBeInTheDocument();
    });
  });

  describe('Error Handling - Initial Load Failures', () => {
    it('shows full-page error when initial profile fetch fails (no profile data)', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: null,
        profileError: 'Network error: Failed to fetch profile',
      });

      render(<ProfilePage />);

      expect(screen.getByText('Failed to Load Profile')).toBeInTheDocument();
      expect(screen.getByText('Network error: Failed to fetch profile')).toBeInTheDocument();

      // Should not show the main profile content
      expect(screen.queryByText('My Profile')).not.toBeInTheDocument();
    });

    it('returns null when profile is missing without error', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: null,
        profileError: null,
        isLoadingProfile: false,
      });

      const { container } = render(<ProfilePage />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Error Handling - Profile Refresh Failures', () => {
    it('shows inline error when profile refresh fails but stale data exists', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: mockProfile,
        profileError: 'Failed to refresh profile data',
      });

      render(<ProfilePage />);

      // Should show the inline error with specific title
      expect(screen.getByText('Failed to Refresh Profile')).toBeInTheDocument();
      expect(screen.getByText('Failed to refresh profile data')).toBeInTheDocument();

      // Should still show the main profile content with stale data
      expect(screen.getByText('My Profile')).toBeInTheDocument();
      expect(screen.getByText('testuser')).toBeInTheDocument();
    });

    it('displays both profile refresh error and stale profile data simultaneously', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: mockProfile,
        profileError: 'Session expired',
      });

      render(<ProfilePage />);

      // Error should be visible
      expect(screen.getByText('Failed to Refresh Profile')).toBeInTheDocument();
      expect(screen.getByText('Session expired')).toBeInTheDocument();

      // Stale profile data should still be displayed
      expect(screen.getByText('testuser')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });

  describe('Error Handling - Mutation Errors', () => {
    it('shows mutation error for password change failures', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        mutationError: 'Incorrect current password',
      });

      render(<ProfilePage />);

      expect(screen.getByText('Incorrect current password')).toBeInTheDocument();
      expect(screen.getByText('My Profile')).toBeInTheDocument();
    });

    it('shows mutation error for session deletion failures', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        mutationError: 'Failed to delete session',
      });

      render(<ProfilePage />);

      expect(screen.getByText('Failed to delete session')).toBeInTheDocument();
    });
  });

  describe('Error Handling - Multiple Errors', () => {
    it('displays both profileError and mutationError when both exist', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: mockProfile,
        profileError: 'Failed to refresh profile',
        mutationError: 'Failed to change password',
      });

      render(<ProfilePage />);

      // Both errors should be visible
      expect(screen.getByText('Failed to Refresh Profile')).toBeInTheDocument();
      expect(screen.getByText('Failed to refresh profile')).toBeInTheDocument();
      expect(screen.getByText('Failed to change password')).toBeInTheDocument();
    });

    it('does not show profileError inline when profile is null (only full-page error)', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: null,
        profileError: 'Initial load failed',
      });

      render(<ProfilePage />);

      // Should show full-page error, not inline error
      expect(screen.getByText('Failed to Load Profile')).toBeInTheDocument();
      expect(screen.queryByText('Failed to Refresh Profile')).not.toBeInTheDocument();
    });
  });

  describe('Successful Profile Display', () => {
    it('renders profile page with all sections when no errors', () => {
      vi.mocked(useProfile).mockReturnValue(defaultHookReturn);

      render(<ProfilePage />);

      expect(screen.getByText('My Profile')).toBeInTheDocument();
      expect(screen.getByText(/manage your account settings/i)).toBeInTheDocument();

      // Should not show any error messages
      expect(screen.queryByText(/failed/i)).not.toBeInTheDocument();
    });

    it('renders all main sections', () => {
      vi.mocked(useProfile).mockReturnValue(defaultHookReturn);

      render(<ProfilePage />);

      // Profile information section
      expect(screen.getByText('testuser')).toBeInTheDocument();

      // Change password section should be present (there are multiple, check for heading)
      expect(screen.getByRole('heading', { name: /change password/i })).toBeInTheDocument();

      // Sessions section should be present
      expect(screen.getByRole('heading', { name: /active sessions/i })).toBeInTheDocument();
    });
  });

  describe('Sessions Error Handling', () => {
    it('passes sessionsError to SessionsList component and displays error', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        sessionsError: 'Failed to load sessions',
      });

      render(<ProfilePage />);

      // The SessionsList component should display the error
      expect(screen.getByText('My Profile')).toBeInTheDocument();
      expect(screen.getByText('Failed to Load Sessions')).toBeInTheDocument();
      expect(screen.getByText('Failed to load sessions')).toBeInTheDocument();
    });

    it('handles sessionsError independently from profileError', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: mockProfile,
        sessions: [],
        profileError: null,
        sessionsError: 'Session service unavailable',
      });

      render(<ProfilePage />);

      // Profile should be displayed normally
      expect(screen.getByText('testuser')).toBeInTheDocument();

      // Sessions error should be displayed within SessionsList
      expect(screen.getByText('Failed to Load Sessions')).toBeInTheDocument();
      expect(screen.getByText('Session service unavailable')).toBeInTheDocument();

      // No profile error should be shown
      expect(screen.queryByText('Failed to Refresh Profile')).not.toBeInTheDocument();
    });

    it('displays all three error types simultaneously when all fail', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        profile: mockProfile,
        sessions: [],
        profileError: 'Profile refresh failed',
        sessionsError: 'Sessions fetch failed',
        mutationError: 'Password change failed',
      });

      render(<ProfilePage />);

      // All three errors should be visible
      expect(screen.getByText('Failed to Refresh Profile')).toBeInTheDocument();
      expect(screen.getByText('Profile refresh failed')).toBeInTheDocument();

      expect(screen.getByText('Password change failed')).toBeInTheDocument();

      expect(screen.getByText('Failed to Load Sessions')).toBeInTheDocument();
      expect(screen.getByText('Sessions fetch failed')).toBeInTheDocument();
    });

    it('shows sessions loader when loading and no sessions exist', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        sessions: [],
        isLoadingSessions: true,
      });

      render(<ProfilePage />);

      expect(screen.getByText(/loading sessions/i)).toBeInTheDocument();
    });

    it('does not show sessions loader when sessions are already loaded', () => {
      vi.mocked(useProfile).mockReturnValue({
        ...defaultHookReturn,
        sessions: mockSessions,
        isLoadingSessions: true,
      });

      render(<ProfilePage />);

      // Should not show loader since sessions already exist
      expect(screen.queryByText(/loading sessions/i)).not.toBeInTheDocument();
      // Should show the sessions count instead
      expect(screen.getByText(/1 session\(s\)/)).toBeInTheDocument();
    });
  });
});
