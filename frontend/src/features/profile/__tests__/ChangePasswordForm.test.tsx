import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChangePasswordForm } from '../components/ChangePasswordForm';

describe('ChangePasswordForm', () => {
  let mockOnSubmit: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnSubmit = vi.fn().mockResolvedValue(undefined);
  });

  describe('Rendering', () => {
    it('renders all form fields', () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^new password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /change password/i })).toBeInTheDocument();
    });

    it('renders with description text', () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      expect(screen.getByText(/update your password/i)).toBeInTheDocument();
    });

    it('renders help text for password requirements', () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows error when current password is empty', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/current password is required/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows error when new password is empty', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/new password is required/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('validates password length (minimum 8 characters)', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'Short1' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/at least 8 characters long/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('validates password requires uppercase letter', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'lowercase123' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/contain at least one uppercase letter/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('validates password requires lowercase letter', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'UPPERCASE123' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/contain at least one lowercase letter/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('validates password requires digit', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NoDigitsHere' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/contain at least one digit/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows error when passwords do not match', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NewPass123' } });
      fireEvent.change(confirmPassword, { target: { value: 'NewPass456' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows error when new password is same as current', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);

      fireEvent.change(currentPassword, { target: { value: 'SamePass123' } });
      fireEvent.change(newPassword, { target: { value: 'SamePass123' } });
      fireEvent.change(confirmPassword, { target: { value: 'SamePass123' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/must be different from current password/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NewPass456' } });
      fireEvent.change(confirmPassword, { target: { value: 'NewPass456' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith('OldPass123', 'NewPass456');
      });
    });

    it('clears form fields after successful submission', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i) as HTMLInputElement;
      const newPassword = screen.getByLabelText(/^new password$/i) as HTMLInputElement;
      const confirmPassword = screen.getByLabelText(/confirm new password/i) as HTMLInputElement;

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NewPass456' } });
      fireEvent.change(confirmPassword, { target: { value: 'NewPass456' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(currentPassword.value).toBe('');
        expect(newPassword.value).toBe('');
        expect(confirmPassword.value).toBe('');
      });
    });

    it('shows success message after successful submission', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NewPass456' } });
      fireEvent.change(confirmPassword, { target: { value: 'NewPass456' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/password changed successfully/i)).toBeInTheDocument();
      });
    });

    it('allows manual dismissal of success message', async () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NewPass456' } });
      fireEvent.change(confirmPassword, { target: { value: 'NewPass456' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/password changed successfully/i)).toBeInTheDocument();
      });

      const dismissButton = screen.getByRole('button', { name: /dismiss success message/i });
      fireEvent.click(dismissButton);

      await waitFor(() => {
        expect(screen.queryByText(/password changed successfully/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays generic error message on submission failure', async () => {
      mockOnSubmit.mockRejectedValue(new Error('Something went wrong'));

      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NewPass456' } });
      fireEvent.change(confirmPassword, { target: { value: 'NewPass456' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
      });
    });

    it('displays specific error for incorrect current password', async () => {
      mockOnSubmit.mockRejectedValue(new Error('401: Unauthorized'));

      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);

      fireEvent.change(currentPassword, { target: { value: 'WrongPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NewPass456' } });
      fireEvent.change(confirmPassword, { target: { value: 'NewPass456' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/current password is incorrect/i)).toBeInTheDocument();
      });
    });

    it('displays specific error for network issues', async () => {
      mockOnSubmit.mockRejectedValue(new Error('network error'));

      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NewPass456' } });
      fireEvent.change(confirmPassword, { target: { value: 'NewPass456' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network error.*check your connection/i)).toBeInTheDocument();
      });
    });

    it('displays specific error for validation failures', async () => {
      mockOnSubmit.mockRejectedValue(new Error('400: Validation failed'));

      render(<ChangePasswordForm onSubmit={mockOnSubmit} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);

      fireEvent.change(currentPassword, { target: { value: 'OldPass123' } });
      fireEvent.change(newPassword, { target: { value: 'NewPass456' } });
      fireEvent.change(confirmPassword, { target: { value: 'NewPass456' } });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/password validation failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('disables all inputs during loading', () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} isLoading={true} />);

      const currentPassword = screen.getByLabelText(/current password/i);
      const newPassword = screen.getByLabelText(/^new password$/i);
      const confirmPassword = screen.getByLabelText(/confirm new password/i);
      const submitButton = screen.getByRole('button', { name: /change password/i });

      expect(currentPassword).toBeDisabled();
      expect(newPassword).toBeDisabled();
      expect(confirmPassword).toBeDisabled();
      expect(submitButton).toBeDisabled();
    });

    it('shows loading state on submit button', () => {
      render(<ChangePasswordForm onSubmit={mockOnSubmit} isLoading={true} />);

      const submitButton = screen.getByRole('button', { name: /change password/i });
      expect(submitButton).toHaveClass('btn-loading');
    });
  });
});
