import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SessionsList } from '../components/SessionsList';
import type { Session } from '../types';

describe('SessionsList', () => {
  let mockOnDeleteSession: ReturnType<typeof vi.fn>;

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
    {
      id: 'session-3',
      created_at: '2024-12-18T08:00:00Z',
      last_accessed: '2024-12-20T12:00:00Z',
      is_current: false,
    },
  ];

  beforeEach(() => {
    mockOnDeleteSession = vi.fn().mockResolvedValue(undefined);
  });

  describe('Rendering', () => {
    it('renders sessions list with all sessions', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      expect(screen.getByRole('heading', { name: /active sessions/i })).toBeInTheDocument();
      expect(screen.getByText(/3 session\(s\)/i)).toBeInTheDocument();
    });

    it('renders empty state when no sessions', () => {
      render(<SessionsList sessions={[]} onDeleteSession={mockOnDeleteSession} />);

      expect(screen.getByText(/no active sessions found/i)).toBeInTheDocument();
    });

    it('renders description text', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      expect(screen.getByText(/manage your active sessions/i)).toBeInTheDocument();
    });

    it('displays session count correctly', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      expect(screen.getByText('3 session(s)')).toBeInTheDocument();
    });

    it('displays correct count for single session', () => {
      const singleSession = [mockSessions[0]];
      render(<SessionsList sessions={singleSession} onDeleteSession={mockOnDeleteSession} />);

      expect(screen.getByText('1 session(s)')).toBeInTheDocument();
    });
  });

  describe('Current Session Badge', () => {
    it('displays "Current Session" badge for current session', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      expect(screen.getByText(/current session/i)).toBeInTheDocument();
    });

    it('applies correct CSS class to current session', () => {
      const { container } = render(
        <SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />
      );

      const currentSessionElement = container.querySelector('.session-item.current');
      expect(currentSessionElement).toBeInTheDocument();
    });

    it('does not show logout button for current session', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      // Should have 2 logout buttons (for non-current sessions only)
      const logoutButtons = screen.getAllByRole('button', { name: /logout/i });
      expect(logoutButtons).toHaveLength(2);
    });
  });

  describe('Session Information Display', () => {
    it('displays created date for each session', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const createdLabels = screen.getAllByText(/created:/i);
      expect(createdLabels).toHaveLength(3);
    });

    it('displays last active date for each session', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const lastActiveLabels = screen.getAllByText(/last active:/i);
      expect(lastActiveLabels).toHaveLength(3);
    });

    it('formats dates correctly', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      // Check that dates are displayed (format depends on locale)
      const dateElements = screen.getAllByText(/2024/);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  describe('Logout Functionality', () => {
    it('shows logout button for non-current sessions', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      expect(logoutButtons).toHaveLength(2); // Only for session-2 and session-3
    });

    it('opens confirmation modal when logout is clicked', async () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      fireEvent.click(logoutButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/confirm logout/i)).toBeInTheDocument();
        expect(screen.getByText(/are you sure you want to log out/i)).toBeInTheDocument();
      });
    });

    it('shows confirmation dialog content', async () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      fireEvent.click(logoutButtons[0]);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /confirm logout/i })).toBeInTheDocument();
      });
    });

    it('closes modal when cancel is clicked', async () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      fireEvent.click(logoutButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/confirm logout/i)).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText(/confirm logout/i)).not.toBeInTheDocument();
      });

      expect(mockOnDeleteSession).not.toHaveBeenCalled();
    });

    it('calls onDeleteSession when confirmed', async () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      fireEvent.click(logoutButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/confirm logout/i)).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm logout/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockOnDeleteSession).toHaveBeenCalledWith('session-2');
      });
    });

    it('closes modal after successful deletion', async () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      fireEvent.click(logoutButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/confirm logout/i)).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm logout/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.queryByText(/confirm logout/i)).not.toBeInTheDocument();
      });
    });

    it('shows loading state during deletion', async () => {
      mockOnDeleteSession.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      fireEvent.click(logoutButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/confirm logout/i)).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm logout/i });
      fireEvent.click(confirmButton);

      // Check that button is in loading state
      await waitFor(() => {
        expect(confirmButton).toHaveClass('btn-loading');
        expect(confirmButton).toBeDisabled();
      });
    });

    it('handles deletion errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockOnDeleteSession.mockRejectedValue(new Error('Deletion failed'));

      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      fireEvent.click(logoutButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/confirm logout/i)).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm logout/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalled();
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Loading State', () => {
    it('disables logout buttons when loading', () => {
      render(
        <SessionsList
          sessions={mockSessions}
          onDeleteSession={mockOnDeleteSession}
          isLoading={true}
        />
      );

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      logoutButtons.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message when error prop is provided', () => {
      const errorMessage = 'Failed to load sessions';
      render(
        <SessionsList
          sessions={mockSessions}
          onDeleteSession={mockOnDeleteSession}
          error={errorMessage}
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByText('Failed to Load Sessions')).toBeInTheDocument();
    });

    it('does not show empty state when error prop is provided', () => {
      const errorMessage = 'Network error';
      render(
        <SessionsList
          sessions={[]}
          onDeleteSession={mockOnDeleteSession}
          error={errorMessage}
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.queryByText('No active sessions found.')).toBeNull();
    });

    it('does not render sessions list when error prop is provided', () => {
      const errorMessage = 'Server error';
      render(
        <SessionsList
          sessions={mockSessions}
          onDeleteSession={mockOnDeleteSession}
          error={errorMessage}
        />
      );

      // Error state still shows the heading but not the session count or full description
      expect(screen.getByRole('heading', { name: 'Active Sessions' })).toBeInTheDocument();
      expect(screen.queryByText('3 session(s)')).toBeNull();
      expect(screen.queryByText('Manage your active sessions across different devices. You can log out from other devices remotely for security.')).toBeNull();
      // Should show the shorter description from error state
      expect(screen.getByText('Manage your active sessions across different devices.')).toBeInTheDocument();
    });

    it('shows empty state when no error and no sessions', () => {
      render(
        <SessionsList
          sessions={[]}
          onDeleteSession={mockOnDeleteSession}
          error={null}
        />
      );

      expect(screen.getByText('No active sessions found.')).toBeInTheDocument();
      expect(screen.queryByText('Failed to Load Sessions')).toBeNull();
    });

    it('prioritizes error over empty state', () => {
      const errorMessage = 'Connection failed';
      render(
        <SessionsList
          sessions={[]}
          onDeleteSession={mockOnDeleteSession}
          error={errorMessage}
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.queryByText('No active sessions found.')).toBeNull();
    });

    it('renders normally when error is null or undefined', () => {
      render(
        <SessionsList
          sessions={mockSessions}
          onDeleteSession={mockOnDeleteSession}
          error={null}
        />
      );

      expect(screen.getByRole('heading', { name: 'Active Sessions' })).toBeInTheDocument();
      expect(screen.getByText('3 session(s)')).toBeInTheDocument();
      expect(screen.queryByText('Failed to Load Sessions')).toBeNull();
    });

    it('handles undefined error prop', () => {
      render(
        <SessionsList
          sessions={mockSessions}
          onDeleteSession={mockOnDeleteSession}
          error={undefined}
        />
      );

      expect(screen.getByRole('heading', { name: 'Active Sessions' })).toBeInTheDocument();
      expect(screen.queryByText('Failed to Load Sessions')).toBeNull();
    });
  });

  describe('Accessibility', () => {
    it('uses semantic HTML for sessions list', () => {
      const { container } = render(
        <SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />
      );

      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      expect(container.querySelector('.sessions-items')).toBeInTheDocument();
    });

    it('has accessible modal with proper ARIA attributes', async () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      fireEvent.click(logoutButtons[0]);

      await waitFor(() => {
        const modal = screen.getByRole('dialog');
        expect(modal).toBeInTheDocument();
      });
    });

    it('has descriptive button labels', () => {
      render(<SessionsList sessions={mockSessions} onDeleteSession={mockOnDeleteSession} />);

      const logoutButtons = screen.getAllByRole('button', { name: /^logout$/i });
      expect(logoutButtons.length).toBeGreaterThan(0);
    });
  });
});
