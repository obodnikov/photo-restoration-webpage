/**
 * ForcePasswordChangePage component tests
 * Tests the forced password change flow, validation, and user interactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ForcePasswordChangePage } from '../pages/ForcePasswordChangePage';
import * as api from '../../../services/apiClient';
import { useAuthStore } from '../../../services/authStore';

// Mock dependencies
vi.mock('../../../services/apiClient', () => ({
  put: vi.fn(),
}));

vi.mock('../../../services/authStore', () => ({
  useAuthStore: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Wrapper component for router context
const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('ForcePasswordChangePage', () => {
  const mockClearAuth = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useAuthStore to handle selector function
    vi.mocked(useAuthStore).mockImplementation((selector: any) => {
      const state = { clearAuth: mockClearAuth };
      return selector ? selector(state) : state;
    });
  });

  describe('Rendering', () => {
    it('renders form with all required fields', () => {
      renderWithRouter(<ForcePasswordChangePage />);

      expect(screen.getByText('Password Change Required')).toBeInTheDocument();
      expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^new password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument();
    });

    it('displays warning message', () => {
      renderWithRouter(<ForcePasswordChangePage />);

      expect(
        screen.getByText(/for security reasons, you must change your password/i)
      ).toBeInTheDocument();
    });

    it('renders submit and logout buttons', () => {
      renderWithRouter(<ForcePasswordChangePage />);

      expect(screen.getByRole('button', { name: /change password/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
    });

    it('displays password requirements hint', () => {
      renderWithRouter(<ForcePasswordChangePage />);

      expect(
        screen.getByText(/must be at least 8 characters with uppercase, lowercase, and digits/i)
      ).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('shows error when all fields are empty', async () => {
      renderWithRouter(<ForcePasswordChangePage />);

      const form = screen.getByRole('button', { name: /change password/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      await waitFor(() => {
        expect(screen.getByText('All fields are required')).toBeInTheDocument();
      });
    });

    it('shows error when password is less than 8 characters', async () => {
      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass1' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'Short1' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'Short1' },
      });

      const form = screen.getByRole('button', { name: /change password/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      await waitFor(() => {
        expect(
          screen.getByText('New password must be at least 8 characters long')
        ).toBeInTheDocument();
      });
    });

    it('shows error when password lacks uppercase letter', async () => {
      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass1' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'newpass123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'newpass123' },
      });

      const form = screen.getByRole('button', { name: /change password/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      await waitFor(() => {
        expect(
          screen.getByText('New password must contain at least one uppercase letter')
        ).toBeInTheDocument();
      });
    });

    it('shows error when password lacks lowercase letter', async () => {
      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass1' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'NEWPASS123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'NEWPASS123' },
      });

      const form = screen.getByRole('button', { name: /change password/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      await waitFor(() => {
        expect(
          screen.getByText('New password must contain at least one lowercase letter')
        ).toBeInTheDocument();
      });
    });

    it('shows error when password lacks digit', async () => {
      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass1' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'NewPassword' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'NewPassword' },
      });

      const form = screen.getByRole('button', { name: /change password/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      await waitFor(() => {
        expect(
          screen.getByText('New password must contain at least one digit')
        ).toBeInTheDocument();
      });
    });

    it('shows error when passwords do not match', async () => {
      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass1' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'NewPass123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'NewPass456' },
      });

      const form = screen.getByRole('button', { name: /change password/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      await waitFor(() => {
        expect(screen.getByText('New passwords do not match')).toBeInTheDocument();
      });
    });

    it('shows error when new password equals current password', async () => {
      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'SamePass123' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'SamePass123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'SamePass123' },
      });

      const form = screen.getByRole('button', { name: /change password/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      await waitFor(() => {
        expect(
          screen.getByText('New password must be different from current password')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Submission Flow', () => {
    it('successfully changes password and redirects to login', async () => {
      vi.mocked(api.put).mockResolvedValueOnce({ success: true });

      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass123' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'NewPass123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'NewPass123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /change password/i }));

      await waitFor(() => {
        expect(api.put).toHaveBeenCalledWith('/users/me/password', {
          current_password: 'OldPass123',
          new_password: 'NewPass123',
        });
      });

      expect(mockClearAuth).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/login', {
        state: {
          message: 'Password changed successfully! Please login with your new password.',
        },
      });
    });

    it('displays API error message on failure', async () => {
      const errorMessage = 'Current password is incorrect';
      vi.mocked(api.put).mockRejectedValueOnce(new Error(errorMessage));

      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'WrongPass123' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'NewPass123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'NewPass123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /change password/i }));

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      expect(mockClearAuth).not.toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('displays generic error for non-Error exceptions', async () => {
      vi.mocked(api.put).mockRejectedValueOnce('Network failure');

      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass123' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'NewPass123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'NewPass123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /change password/i }));

      await waitFor(() => {
        expect(
          screen.getByText('Failed to change password. Please try again.')
        ).toBeInTheDocument();
      });
    });

    it('shows loading state during submission', async () => {
      vi.mocked(api.put).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass123' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'NewPass123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'NewPass123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /change password/i }));

      // Check that fields are disabled during loading
      await waitFor(() => {
        expect(screen.getByLabelText(/current password/i)).toBeDisabled();
        expect(screen.getByLabelText(/^new password$/i)).toBeDisabled();
        expect(screen.getByLabelText(/confirm new password/i)).toBeDisabled();
      });
    });
  });

  describe('User Interactions', () => {
    it('logout button clears auth and redirects to login', () => {
      renderWithRouter(<ForcePasswordChangePage />);

      const logoutButton = screen.getByRole('button', { name: /logout/i });
      fireEvent.click(logoutButton);

      expect(mockClearAuth).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('clears error when submitting again after validation error', async () => {
      renderWithRouter(<ForcePasswordChangePage />);

      // First submission - trigger validation error
      const form = screen.getByRole('button', { name: /change password/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      await waitFor(() => {
        expect(screen.getByText('All fields are required')).toBeInTheDocument();
      });

      // Fill in fields and submit again
      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass123' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'NewPass123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'NewPass123' },
      });

      vi.mocked(api.put).mockResolvedValueOnce({ success: true });
      if (form) {
        fireEvent.submit(form);
      }

      // Error should be cleared during submission
      await waitFor(() => {
        expect(screen.queryByText('All fields are required')).not.toBeInTheDocument();
      });
    });

    it('buttons are disabled during loading state', async () => {
      vi.mocked(api.put).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      renderWithRouter(<ForcePasswordChangePage />);

      fireEvent.change(screen.getByLabelText(/current password/i), {
        target: { value: 'OldPass123' },
      });
      fireEvent.change(screen.getByLabelText(/^new password$/i), {
        target: { value: 'NewPass123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm new password/i), {
        target: { value: 'NewPass123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /change password/i }));

      // Check that both buttons are disabled during loading
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /change password/i })).toBeDisabled();
        expect(screen.getByRole('button', { name: /logout/i })).toBeDisabled();
      });
    });
  });
});
