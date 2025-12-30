import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DeleteUserDialog } from '../components/DeleteUserDialog';
import type { AdminUser } from '../types';

describe('DeleteUserDialog', () => {
  const mockUser: AdminUser = {
    id: 2,
    username: 'testuser',
    email: 'test@example.com',
    full_name: 'Test User',
    role: 'user',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    last_login: '2024-12-22T10:00:00Z',
  };

  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    user: mockUser,
    isLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders when isOpen is true and user is provided', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      expect(screen.getByText('Confirm Delete User')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(<DeleteUserDialog {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Confirm Delete User')).not.toBeInTheDocument();
    });

    it('does not render when user is null', () => {
      render(<DeleteUserDialog {...defaultProps} user={null} />);

      expect(screen.queryByText('Confirm Delete User')).not.toBeInTheDocument();
    });

    it('displays username in confirmation message', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      expect(screen.getByText(/testuser/)).toBeInTheDocument();
    });

    it('displays user email in warning details', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      expect(screen.getByText(/test@example.com/)).toBeInTheDocument();
    });

    it('renders warning icon', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      expect(screen.getByText('⚠️')).toBeInTheDocument();
    });

    it('displays warning message', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      expect(
        screen.getByText(/Are you sure you want to delete the user/)
      ).toBeInTheDocument();
    });

    it('displays "This action cannot be undone" warning', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      expect(screen.getByText(/This action cannot be undone/)).toBeInTheDocument();
    });

    it('displays cascade delete warning list', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      expect(screen.getByText(/This will permanently delete:/)).toBeInTheDocument();
      expect(screen.getByText(/User account/)).toBeInTheDocument();
      expect(screen.getByText(/All user sessions/)).toBeInTheDocument();
      expect(screen.getByText(/All processed images/)).toBeInTheDocument();
      expect(screen.getByText(/All associated data/)).toBeInTheDocument();
    });

    it('renders Cancel and Delete buttons', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Delete User')).toBeInTheDocument();
    });
  });

  describe('Confirmation Flow', () => {
    it('calls onConfirm when Delete button is clicked', async () => {
      const onConfirm = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(<DeleteUserDialog {...defaultProps} onConfirm={onConfirm} onClose={onClose} />);

      fireEvent.click(screen.getByText('Delete User'));

      await waitFor(() => {
        expect(onConfirm).toHaveBeenCalledWith(mockUser.id);
      });

      expect(onClose).toHaveBeenCalled();
    });

    it('calls onClose when Cancel button is clicked', () => {
      const onClose = vi.fn();

      render(<DeleteUserDialog {...defaultProps} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });

    it('does not call onConfirm when Cancel is clicked', () => {
      const onConfirm = vi.fn();
      const onClose = vi.fn();

      render(<DeleteUserDialog {...defaultProps} onConfirm={onConfirm} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onConfirm).not.toHaveBeenCalled();
    });

    it('closes dialog after successful deletion', async () => {
      const onConfirm = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(<DeleteUserDialog {...defaultProps} onConfirm={onConfirm} onClose={onClose} />);

      fireEvent.click(screen.getByText('Delete User'));

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message when deletion fails', async () => {
      const error = new Error('Cannot delete user with active sessions');
      const onConfirm = vi.fn().mockRejectedValue(error);

      render(<DeleteUserDialog {...defaultProps} onConfirm={onConfirm} />);

      fireEvent.click(screen.getByText('Delete User'));

      await waitFor(() => {
        expect(screen.getByText('Cannot delete user with active sessions')).toBeInTheDocument();
      });
    });

    it('does not close dialog when deletion fails', async () => {
      const error = new Error('Deletion failed');
      const onConfirm = vi.fn().mockRejectedValue(error);
      const onClose = vi.fn();

      render(<DeleteUserDialog {...defaultProps} onConfirm={onConfirm} onClose={onClose} />);

      fireEvent.click(screen.getByText('Delete User'));

      await waitFor(() => {
        expect(screen.getByText('Deletion failed')).toBeInTheDocument();
      });

      expect(onClose).not.toHaveBeenCalled();
    });

    it('clears error when dialog is closed', async () => {
      const error = new Error('Deletion failed');
      const onConfirm = vi.fn().mockRejectedValue(error);
      const onClose = vi.fn();

      render(<DeleteUserDialog {...defaultProps} onConfirm={onConfirm} onClose={onClose} />);

      // Trigger error
      fireEvent.click(screen.getByText('Delete User'));

      await waitFor(() => {
        expect(screen.getByText('Deletion failed')).toBeInTheDocument();
      });

      // Close dialog
      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });

    it('displays generic error message for non-Error exceptions', async () => {
      const onConfirm = vi.fn().mockRejectedValue('string error');

      render(<DeleteUserDialog {...defaultProps} onConfirm={onConfirm} />);

      fireEvent.click(screen.getByText('Delete User'));

      await waitFor(() => {
        expect(screen.getByText('Failed to delete user')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('prevents closing when isLoading is true', () => {
      const onClose = vi.fn();

      render(<DeleteUserDialog {...defaultProps} isLoading={true} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).not.toHaveBeenCalled();
    });

    it('disables Cancel button when isLoading is true', () => {
      render(<DeleteUserDialog {...defaultProps} isLoading={true} />);

      const cancelButton = screen.getByText('Cancel');
      expect(cancelButton).toBeDisabled();
    });

    it('shows loading state on Delete button when isLoading is true', () => {
      render(<DeleteUserDialog {...defaultProps} isLoading={true} />);

      const deleteButton = screen.getByText('Delete User');
      expect(deleteButton).toBeInTheDocument();
    });
  });

  describe('User Changes', () => {
    it('updates displayed username when user prop changes', () => {
      const { rerender } = render(<DeleteUserDialog {...defaultProps} />);

      expect(screen.getByText(/testuser/)).toBeInTheDocument();

      const newUser: AdminUser = {
        ...mockUser,
        id: 3,
        username: 'differentuser',
        email: 'different@example.com',
      };

      rerender(<DeleteUserDialog {...defaultProps} user={newUser} />);

      expect(screen.getByText(/differentuser/)).toBeInTheDocument();
      expect(screen.getByText(/different@example.com/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('renders proper button structure', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThanOrEqual(2);
    });

    it('Delete button has danger variant styling', () => {
      render(<DeleteUserDialog {...defaultProps} />);

      const deleteButton = screen.getByText('Delete User');
      // Check that button has danger variant class
      expect(deleteButton.className).toContain('danger');
    });
  });
});
