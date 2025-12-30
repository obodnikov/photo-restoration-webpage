import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EditUserDialog } from '../components/EditUserDialog';
import type { AdminUser } from '../types';

describe('EditUserDialog', () => {
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
    onSubmit: vi.fn(),
    user: mockUser,
    isLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders when isOpen is true and user is provided', () => {
      render(<EditUserDialog {...defaultProps} />);

      expect(screen.getByText('Edit User: testuser')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(<EditUserDialog {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Edit User: testuser')).not.toBeInTheDocument();
    });

    it('does not render when user is null', () => {
      render(<EditUserDialog {...defaultProps} user={null} />);

      expect(screen.queryByText(/Edit User:/)).not.toBeInTheDocument();
    });

    it('renders all form fields', () => {
      render(<EditUserDialog {...defaultProps} />);

      expect(screen.getByLabelText(/Email/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Full Name/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Role/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Active/)).toBeInTheDocument();
    });

    it('renders submit and cancel buttons', () => {
      render(<EditUserDialog {...defaultProps} />);

      expect(screen.getByText('Save Changes')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('pre-fills form with user data', () => {
      render(<EditUserDialog {...defaultProps} />);

      const emailInput = screen.getByLabelText(/Email/) as HTMLInputElement;
      const fullNameInput = screen.getByLabelText(/Full Name/) as HTMLInputElement;
      const roleSelect = screen.getByLabelText(/Role/) as HTMLSelectElement;
      const activeCheckbox = screen.getByLabelText(/Active/) as HTMLInputElement;

      expect(emailInput.value).toBe(mockUser.email);
      expect(fullNameInput.value).toBe(mockUser.full_name);
      expect(roleSelect.value).toBe(mockUser.role);
      expect(activeCheckbox.checked).toBe(mockUser.is_active);
    });

    it('displays username in title', () => {
      render(<EditUserDialog {...defaultProps} />);

      expect(screen.getByText('Edit User: testuser')).toBeInTheDocument();
    });

    it('displays current user info text', () => {
      render(<EditUserDialog {...defaultProps} />);

      expect(screen.getByText(/Username cannot be changed/)).toBeInTheDocument();
      expect(screen.getByText(/testuser/)).toBeInTheDocument();
    });
  });

  describe('Form Updates', () => {
    it('updates email field', () => {
      render(<EditUserDialog {...defaultProps} />);

      const emailInput = screen.getByLabelText(/Email/) as HTMLInputElement;
      fireEvent.change(emailInput, { target: { value: 'newemail@example.com' } });

      expect(emailInput.value).toBe('newemail@example.com');
    });

    it('updates full name field', () => {
      render(<EditUserDialog {...defaultProps} />);

      const fullNameInput = screen.getByLabelText(/Full Name/) as HTMLInputElement;
      fireEvent.change(fullNameInput, { target: { value: 'Updated Name' } });

      expect(fullNameInput.value).toBe('Updated Name');
    });

    it('updates role field', () => {
      render(<EditUserDialog {...defaultProps} />);

      const roleSelect = screen.getByLabelText(/Role/) as HTMLSelectElement;
      fireEvent.change(roleSelect, { target: { value: 'admin' } });

      expect(roleSelect.value).toBe('admin');
    });

    it('toggles is_active checkbox', () => {
      render(<EditUserDialog {...defaultProps} />);

      const activeCheckbox = screen.getByLabelText(/Active/) as HTMLInputElement;
      expect(activeCheckbox.checked).toBe(true);

      fireEvent.click(activeCheckbox);
      expect(activeCheckbox.checked).toBe(false);

      fireEvent.click(activeCheckbox);
      expect(activeCheckbox.checked).toBe(true);
    });
  });

  describe('Form Submission', () => {
    it('submits only changed fields', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(<EditUserDialog {...defaultProps} onSubmit={onSubmit} onClose={onClose} />);

      // Change only email
      const emailInput = screen.getByLabelText(/Email/);
      fireEvent.change(emailInput, { target: { value: 'updated@example.com' } });

      fireEvent.click(screen.getByText('Save Changes'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(mockUser.id, {
          email: 'updated@example.com',
        });
      });

      expect(onClose).toHaveBeenCalled();
    });

    it('submits multiple changed fields', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);

      render(<EditUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'updated@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'New Name' } });
      fireEvent.change(screen.getByLabelText(/Role/), { target: { value: 'admin' } });

      fireEvent.click(screen.getByText('Save Changes'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(mockUser.id, {
          email: 'updated@example.com',
          full_name: 'New Name',
          role: 'admin',
        });
      });
    });

    it('submits when only is_active is changed', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);

      render(<EditUserDialog {...defaultProps} onSubmit={onSubmit} />);

      const activeCheckbox = screen.getByLabelText(/Active/);
      fireEvent.click(activeCheckbox);

      fireEvent.click(screen.getByText('Save Changes'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(mockUser.id, {
          is_active: false,
        });
      });
    });

    it('shows error when no changes are detected', async () => {
      const onSubmit = vi.fn();

      render(<EditUserDialog {...defaultProps} onSubmit={onSubmit} />);

      // Submit without changing anything
      fireEvent.click(screen.getByText('Save Changes'));

      await waitFor(() => {
        expect(screen.getByText('No changes detected')).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('handles submission errors', async () => {
      const error = new Error('Email already in use');
      const onSubmit = vi.fn().mockRejectedValue(error);

      render(<EditUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'duplicate@example.com' },
      });

      fireEvent.click(screen.getByText('Save Changes'));

      await waitFor(() => {
        expect(screen.getByText('Email already in use')).toBeInTheDocument();
      });
    });

    it('clears error on successful submission', async () => {
      const error = new Error('Temporary error');
      const onSubmit = vi
        .fn()
        .mockRejectedValueOnce(error)
        .mockResolvedValue(undefined);

      render(<EditUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'first@example.com' },
      });

      // First submission - error
      fireEvent.click(screen.getByText('Save Changes'));
      await waitFor(() => {
        expect(screen.getByText('Temporary error')).toBeInTheDocument();
      });

      // Second submission - success
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'second@example.com' },
      });
      fireEvent.click(screen.getByText('Save Changes'));

      await waitFor(() => {
        expect(screen.queryByText('Temporary error')).not.toBeInTheDocument();
      });
    });
  });

  describe('Dialog Controls', () => {
    it('calls onClose when Cancel button is clicked', () => {
      const onClose = vi.fn();

      render(<EditUserDialog {...defaultProps} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });

    it('prevents closing when isLoading is true', () => {
      const onClose = vi.fn();

      render(<EditUserDialog {...defaultProps} isLoading={true} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).not.toHaveBeenCalled();
    });

    it('clears error when dialog is closed', () => {
      const onClose = vi.fn();
      const onSubmit = vi.fn().mockRejectedValue(new Error('Test error'));

      render(<EditUserDialog {...defaultProps} onSubmit={onSubmit} onClose={onClose} />);

      // Trigger error
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'error@example.com' },
      });
      fireEvent.click(screen.getByText('Save Changes'));

      // Close dialog
      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });

    it('disables form inputs when isLoading is true', () => {
      render(<EditUserDialog {...defaultProps} isLoading={true} />);

      expect(screen.getByLabelText(/Email/)).toBeDisabled();
      expect(screen.getByLabelText(/Full Name/)).toBeDisabled();
      expect(screen.getByLabelText(/Role/)).toBeDisabled();
      expect(screen.getByLabelText(/Active/)).toBeDisabled();
    });
  });

  describe('User Changes', () => {
    it('updates form when user prop changes', () => {
      const { rerender } = render(<EditUserDialog {...defaultProps} />);

      const newUser: AdminUser = {
        ...mockUser,
        id: 3,
        username: 'otheruser',
        email: 'other@example.com',
        full_name: 'Other User',
      };

      rerender(<EditUserDialog {...defaultProps} user={newUser} />);

      const emailInput = screen.getByLabelText(/Email/) as HTMLInputElement;
      const fullNameInput = screen.getByLabelText(/Full Name/) as HTMLInputElement;

      expect(emailInput.value).toBe('other@example.com');
      expect(fullNameInput.value).toBe('Other User');
      expect(screen.getByText('Edit User: otheruser')).toBeInTheDocument();
    });

    it('clears error when user prop changes', async () => {
      const onSubmit = vi.fn().mockRejectedValue(new Error('Submit error'));
      const { rerender } = render(<EditUserDialog {...defaultProps} onSubmit={onSubmit} />);

      // Trigger error
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'error@example.com' },
      });
      fireEvent.click(screen.getByText('Save Changes'));

      await waitFor(() => {
        expect(screen.getByText('Submit error')).toBeInTheDocument();
      });

      // Change user
      const newUser: AdminUser = {
        ...mockUser,
        id: 3,
        username: 'newuser',
      };

      rerender(<EditUserDialog {...defaultProps} user={newUser} onSubmit={onSubmit} />);

      expect(screen.queryByText('Submit error')).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('requires email field', () => {
      render(<EditUserDialog {...defaultProps} />);

      const emailInput = screen.getByLabelText(/Email/) as HTMLInputElement;
      expect(emailInput).toBeRequired();
    });

    it('requires full name field', () => {
      render(<EditUserDialog {...defaultProps} />);

      const fullNameInput = screen.getByLabelText(/Full Name/) as HTMLInputElement;
      expect(fullNameInput).toBeRequired();
    });

    it('validates email format', () => {
      render(<EditUserDialog {...defaultProps} />);

      const emailInput = screen.getByLabelText(/Email/) as HTMLInputElement;
      expect(emailInput.type).toBe('email');
    });
  });
});
