import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ResetPasswordDialog } from '../components/ResetPasswordDialog';
import * as adminService from '../services/adminService';
import type { AdminUser } from '../types';

// Mock the admin service
vi.mock('../services/adminService', () => ({
  generateRandomPassword: vi.fn(),
}));

describe('ResetPasswordDialog', () => {
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

  let originalCrypto: Crypto;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock crypto for password generation
    originalCrypto = global.crypto;
    const mockGetRandomValues = vi.fn((array: Uint32Array) => {
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 0xffffffff);
      }
      return array;
    });

    global.crypto = {
      getRandomValues: mockGetRandomValues,
    } as unknown as Crypto;

    // Mock generateRandomPassword to return a test password
    vi.mocked(adminService.generateRandomPassword).mockReturnValue('GeneratedPass123!');
  });

  afterEach(() => {
    vi.resetAllMocks();
    global.crypto = originalCrypto;
  });

  describe('Rendering', () => {
    it('renders when isOpen is true and user is provided', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      expect(screen.getByText('Reset Password: testuser')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(<ResetPasswordDialog {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Reset Password: testuser')).not.toBeInTheDocument();
    });

    it('does not render when user is null', () => {
      render(<ResetPasswordDialog {...defaultProps} user={null} />);

      expect(screen.queryByText(/Reset Password:/)).not.toBeInTheDocument();
    });

    it('renders all form fields', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      expect(screen.getByLabelText(/New Password/)).toBeInTheDocument();
      expect(
        screen.getByLabelText(/Require password change on first login/)
      ).toBeInTheDocument();
    });

    it('renders submit and cancel buttons', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      expect(screen.getByText('Reset Password')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('renders Generate password button', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      const generateButtons = screen.getAllByText('Generate');
      expect(generateButtons.length).toBeGreaterThan(0);
    });

    it('renders Show/Hide password button', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      expect(screen.getByText('Show')).toBeInTheDocument();
    });

    it('displays username in title', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      expect(screen.getByText('Reset Password: testuser')).toBeInTheDocument();
    });

    it('has password_must_change checkbox checked by default', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      const checkbox = screen.getByLabelText(
        /Require password change on first login/
      ) as HTMLInputElement;
      expect(checkbox.checked).toBe(true);
    });
  });

  describe('Password Generation', () => {
    it('generates password when Generate button is clicked', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      const generateButtons = screen.getAllByText('Generate');
      fireEvent.click(generateButtons[0]);

      expect(adminService.generateRandomPassword).toHaveBeenCalledWith(12);

      const passwordInput = screen.getByLabelText(/New Password/) as HTMLInputElement;
      expect(passwordInput.value).toBe('GeneratedPass123!');
    });

    it('shows password after generation', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      const generateButtons = screen.getAllByText('Generate');
      fireEvent.click(generateButtons[0]);

      const passwordInput = screen.getByLabelText(/New Password/) as HTMLInputElement;
      expect(passwordInput.type).toBe('text');
    });

    it('handles password generation error', () => {
      const error = new Error('Web Crypto API not available');
      vi.mocked(adminService.generateRandomPassword).mockImplementation(() => {
        throw error;
      });

      render(<ResetPasswordDialog {...defaultProps} />);

      const generateButtons = screen.getAllByText('Generate');
      fireEvent.click(generateButtons[0]);

      expect(screen.getByText('Web Crypto API not available')).toBeInTheDocument();
    });

    it('clears password generation error on successful generation', () => {
      const error = new Error('Web Crypto API not available');
      vi.mocked(adminService.generateRandomPassword)
        .mockImplementationOnce(() => {
          throw error;
        })
        .mockReturnValue('NewPass123!');

      render(<ResetPasswordDialog {...defaultProps} />);

      const generateButtons = screen.getAllByText('Generate');

      // First click - error
      fireEvent.click(generateButtons[0]);
      expect(screen.getByText('Web Crypto API not available')).toBeInTheDocument();

      // Second click - success
      fireEvent.click(generateButtons[0]);
      expect(screen.queryByText('Web Crypto API not available')).not.toBeInTheDocument();
    });
  });

  describe('Password Visibility Toggle', () => {
    it('toggles password visibility when Show/Hide button is clicked', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      const passwordInput = screen.getByLabelText(/New Password/) as HTMLInputElement;
      const showButton = screen.getByText('Show');

      expect(passwordInput.type).toBe('password');

      fireEvent.click(showButton);
      expect(passwordInput.type).toBe('text');
      expect(screen.getByText('Hide')).toBeInTheDocument();

      const hideButton = screen.getByText('Hide');
      fireEvent.click(hideButton);
      expect(passwordInput.type).toBe('password');
    });
  });

  describe('Form Validation', () => {
    it('requires password field', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      const passwordInput = screen.getByLabelText(/New Password/) as HTMLInputElement;
      expect(passwordInput).toBeRequired();
    });

    it('validates password minimum length (8 characters)', async () => {
      const onSubmit = vi.fn();
      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/New Password/), { target: { value: 'Short1' } });
      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('validates password contains uppercase letter', async () => {
      const onSubmit = vi.fn();
      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'lowercase123' },
      });
      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(
          screen.getByText('Password must contain at least one uppercase letter')
        ).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('validates password contains lowercase letter', async () => {
      const onSubmit = vi.fn();
      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'UPPERCASE123' },
      });
      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(
          screen.getByText('Password must contain at least one lowercase letter')
        ).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('validates password contains digit', async () => {
      const onSubmit = vi.fn();
      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/New Password/), { target: { value: 'NoDigits!' } });
      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(
          screen.getByText('Password must contain at least one digit')
        ).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} onClose={onClose} />);

      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'NewSecurePass123!' },
      });

      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(mockUser.id, {
          new_password: 'NewSecurePass123!',
          password_must_change: true,
        });
      });

      expect(onClose).toHaveBeenCalled();
    });

    it('submits with password_must_change disabled', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);

      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'NewSecurePass123!' },
      });

      const checkbox = screen.getByLabelText(/Require password change on first login/);
      fireEvent.click(checkbox);

      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(mockUser.id, {
          new_password: 'NewSecurePass123!',
          password_must_change: false,
        });
      });
    });

    it('displays error on submission failure', async () => {
      const error = new Error('Password does not meet requirements');
      const onSubmit = vi.fn().mockRejectedValue(error);

      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'ValidPass123!' },
      });

      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(screen.getByText('Password does not meet requirements')).toBeInTheDocument();
      });
    });

    it('displays generic error message for non-Error exceptions', async () => {
      const onSubmit = vi.fn().mockRejectedValue('string error');

      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'ValidPass123!' },
      });

      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(screen.getByText('Failed to reset password')).toBeInTheDocument();
      });
    });

    it('resets form after successful submission', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} onClose={onClose} />);

      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'NewSecurePass123!' },
      });

      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });
    });

    it('clears validation error on next submission attempt', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);

      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} />);

      // First submission - validation error
      fireEvent.change(screen.getByLabelText(/New Password/), { target: { value: 'short' } });
      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
      });

      // Second submission - valid password
      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'ValidPass123!' },
      });
      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(
          screen.queryByText('Password must be at least 8 characters long')
        ).not.toBeInTheDocument();
      });
    });
  });

  describe('Dialog Controls', () => {
    it('calls onClose when Cancel button is clicked', () => {
      const onClose = vi.fn();

      render(<ResetPasswordDialog {...defaultProps} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });

    it('clears form state when dialog is closed', () => {
      const onClose = vi.fn();

      render(<ResetPasswordDialog {...defaultProps} onClose={onClose} />);

      // Fill form
      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'SomePassword123!' },
      });

      // Close dialog
      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });

    it('prevents closing when isLoading is true', () => {
      const onClose = vi.fn();

      render(<ResetPasswordDialog {...defaultProps} isLoading={true} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).not.toHaveBeenCalled();
    });

    it('disables form inputs when isLoading is true', () => {
      render(<ResetPasswordDialog {...defaultProps} isLoading={true} />);

      expect(screen.getByLabelText(/New Password/)).toBeDisabled();
      expect(
        screen.getByLabelText(/Require password change on first login/)
      ).toBeDisabled();
    });

    it('clears errors when dialog is closed', async () => {
      const error = new Error('Reset failed');
      const onSubmit = vi.fn().mockRejectedValue(error);
      const onClose = vi.fn();

      render(<ResetPasswordDialog {...defaultProps} onSubmit={onSubmit} onClose={onClose} />);

      // Trigger error
      fireEvent.change(screen.getByLabelText(/New Password/), {
        target: { value: 'ValidPass123!' },
      });
      fireEvent.click(screen.getByText('Reset Password'));

      await waitFor(() => {
        expect(screen.getByText('Reset failed')).toBeInTheDocument();
      });

      // Close dialog
      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Password Must Change Toggle', () => {
    it('toggles password_must_change checkbox', () => {
      render(<ResetPasswordDialog {...defaultProps} />);

      const checkbox = screen.getByLabelText(
        /Require password change on first login/
      ) as HTMLInputElement;

      expect(checkbox.checked).toBe(true);

      fireEvent.click(checkbox);
      expect(checkbox.checked).toBe(false);

      fireEvent.click(checkbox);
      expect(checkbox.checked).toBe(true);
    });
  });

  describe('User Changes', () => {
    it('updates dialog title when user prop changes', () => {
      const { rerender } = render(<ResetPasswordDialog {...defaultProps} />);

      expect(screen.getByText('Reset Password: testuser')).toBeInTheDocument();

      const newUser: AdminUser = {
        ...mockUser,
        id: 3,
        username: 'differentuser',
      };

      rerender(<ResetPasswordDialog {...defaultProps} user={newUser} />);

      expect(screen.getByText('Reset Password: differentuser')).toBeInTheDocument();
    });
  });
});
