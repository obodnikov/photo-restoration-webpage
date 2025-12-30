import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CreateUserDialog } from '../components/CreateUserDialog';
import * as adminService from '../services/adminService';

// Mock the admin service
vi.mock('../services/adminService', () => ({
  generateRandomPassword: vi.fn(),
}));

describe('CreateUserDialog', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn(),
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
    vi.mocked(adminService.generateRandomPassword).mockReturnValue('TestPass123!');
  });

  afterEach(() => {
    vi.resetAllMocks();
    global.crypto = originalCrypto;
  });

  describe('Rendering', () => {
    it('renders when isOpen is true', () => {
      render(<CreateUserDialog {...defaultProps} />);

      expect(screen.getByText('Create New User')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(<CreateUserDialog {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Create New User')).not.toBeInTheDocument();
    });

    it('renders all form fields', () => {
      render(<CreateUserDialog {...defaultProps} />);

      expect(screen.getByLabelText(/Username/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Email/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Full Name/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Temporary Password/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Role/)).toBeInTheDocument();
      expect(
        screen.getByLabelText(/Require password change on first login/)
      ).toBeInTheDocument();
    });

    it('renders submit and cancel buttons', () => {
      render(<CreateUserDialog {...defaultProps} />);

      expect(screen.getByText('Create User')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('renders Generate password button', () => {
      render(<CreateUserDialog {...defaultProps} />);

      const generateButtons = screen.getAllByText('Generate');
      expect(generateButtons.length).toBeGreaterThan(0);
    });

    it('renders Show/Hide password button', () => {
      render(<CreateUserDialog {...defaultProps} />);

      expect(screen.getByText('Show')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('requires username field', () => {
      render(<CreateUserDialog {...defaultProps} />);

      const usernameInput = screen.getByLabelText(/Username/) as HTMLInputElement;
      expect(usernameInput).toBeRequired();
    });

    it('requires email field', () => {
      render(<CreateUserDialog {...defaultProps} />);

      const emailInput = screen.getByLabelText(/Email/) as HTMLInputElement;
      expect(emailInput).toBeRequired();
    });

    it('requires full name field', () => {
      render(<CreateUserDialog {...defaultProps} />);

      const fullNameInput = screen.getByLabelText(/Full Name/) as HTMLInputElement;
      expect(fullNameInput).toBeRequired();
    });

    it('requires password field', () => {
      render(<CreateUserDialog {...defaultProps} />);

      const passwordInput = screen.getByLabelText(/Temporary Password/) as HTMLInputElement;
      expect(passwordInput).toBeRequired();
    });

    it('validates password minimum length (8 characters)', async () => {
      const onSubmit = vi.fn();
      render(<CreateUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'Test User' } });
      fireEvent.change(screen.getByLabelText(/Temporary Password/), {
        target: { value: 'Short1' },
      });

      fireEvent.click(screen.getByText('Create User'));

      await waitFor(() => {
        expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('validates password contains uppercase letter', async () => {
      const onSubmit = vi.fn();
      render(<CreateUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'Test User' } });
      fireEvent.change(screen.getByLabelText(/Temporary Password/), {
        target: { value: 'lowercase123' },
      });

      fireEvent.click(screen.getByText('Create User'));

      await waitFor(() => {
        expect(
          screen.getByText('Password must contain at least one uppercase letter')
        ).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('validates password contains lowercase letter', async () => {
      const onSubmit = vi.fn();
      render(<CreateUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'Test User' } });
      fireEvent.change(screen.getByLabelText(/Temporary Password/), {
        target: { value: 'UPPERCASE123' },
      });

      fireEvent.click(screen.getByText('Create User'));

      await waitFor(() => {
        expect(
          screen.getByText('Password must contain at least one lowercase letter')
        ).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('validates password contains digit', async () => {
      const onSubmit = vi.fn();
      render(<CreateUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'Test User' } });
      fireEvent.change(screen.getByLabelText(/Temporary Password/), {
        target: { value: 'NoDigits!' },
      });

      fireEvent.click(screen.getByText('Create User'));

      await waitFor(() => {
        expect(
          screen.getByText('Password must contain at least one digit')
        ).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('validates email format', () => {
      render(<CreateUserDialog {...defaultProps} />);

      const emailInput = screen.getByLabelText(/Email/) as HTMLInputElement;
      expect(emailInput.type).toBe('email');
    });
  });

  describe('Password Generation', () => {
    it('generates password when Generate button is clicked', () => {
      render(<CreateUserDialog {...defaultProps} />);

      const generateButtons = screen.getAllByText('Generate');
      fireEvent.click(generateButtons[0]);

      expect(adminService.generateRandomPassword).toHaveBeenCalledWith(12);

      const passwordInput = screen.getByLabelText(/Temporary Password/) as HTMLInputElement;
      expect(passwordInput.value).toBe('TestPass123!');
    });

    it('shows password after generation', () => {
      render(<CreateUserDialog {...defaultProps} />);

      const generateButtons = screen.getAllByText('Generate');
      fireEvent.click(generateButtons[0]);

      const passwordInput = screen.getByLabelText(/Temporary Password/) as HTMLInputElement;
      expect(passwordInput.type).toBe('text');
    });

    it('handles password generation error', () => {
      const error = new Error('Web Crypto API not available');
      vi.mocked(adminService.generateRandomPassword).mockImplementation(() => {
        throw error;
      });

      render(<CreateUserDialog {...defaultProps} />);

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

      render(<CreateUserDialog {...defaultProps} />);

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
      render(<CreateUserDialog {...defaultProps} />);

      const passwordInput = screen.getByLabelText(/Temporary Password/) as HTMLInputElement;
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

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(<CreateUserDialog {...defaultProps} onSubmit={onSubmit} onClose={onClose} />);

      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'Test User' } });
      fireEvent.change(screen.getByLabelText(/Temporary Password/), {
        target: { value: 'SecurePass123!' },
      });
      fireEvent.change(screen.getByLabelText(/Role/), { target: { value: 'user' } });

      fireEvent.click(screen.getByText('Create User'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          username: 'testuser',
          email: 'test@example.com',
          full_name: 'Test User',
          password: 'SecurePass123!',
          role: 'user',
          password_must_change: true,
        });
      });

      expect(onClose).toHaveBeenCalled();
    });

    it('submits with admin role', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);

      render(<CreateUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'adminuser' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'admin@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'Admin User' } });
      fireEvent.change(screen.getByLabelText(/Temporary Password/), {
        target: { value: 'AdminPass123!' },
      });
      fireEvent.change(screen.getByLabelText(/Role/), { target: { value: 'admin' } });

      fireEvent.click(screen.getByText('Create User'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          username: 'adminuser',
          email: 'admin@example.com',
          full_name: 'Admin User',
          password: 'AdminPass123!',
          role: 'admin',
          password_must_change: true,
        });
      });
    });

    it('submits with password_must_change disabled', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);

      render(<CreateUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'Test User' } });
      fireEvent.change(screen.getByLabelText(/Temporary Password/), {
        target: { value: 'SecurePass123!' },
      });

      const checkbox = screen.getByLabelText(/Require password change on first login/);
      fireEvent.click(checkbox);

      fireEvent.click(screen.getByText('Create User'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            password_must_change: false,
          })
        );
      });
    });

    it('displays error on submission failure', async () => {
      const error = new Error('Username already exists');
      const onSubmit = vi.fn().mockRejectedValue(error);

      render(<CreateUserDialog {...defaultProps} onSubmit={onSubmit} />);

      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'existing' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'existing@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'Existing User' } });
      fireEvent.change(screen.getByLabelText(/Temporary Password/), {
        target: { value: 'SecurePass123!' },
      });

      fireEvent.click(screen.getByText('Create User'));

      await waitFor(() => {
        expect(screen.getByText('Username already exists')).toBeInTheDocument();
      });
    });

    it('resets form after successful submission', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(<CreateUserDialog {...defaultProps} onSubmit={onSubmit} onClose={onClose} />);

      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Full Name/), { target: { value: 'Test User' } });
      fireEvent.change(screen.getByLabelText(/Temporary Password/), {
        target: { value: 'SecurePass123!' },
      });

      fireEvent.click(screen.getByText('Create User'));

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });
    });
  });

  describe('Dialog Controls', () => {
    it('calls onClose when Cancel button is clicked', () => {
      const onClose = vi.fn();

      render(<CreateUserDialog {...defaultProps} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });

    it('clears form state when dialog is closed', () => {
      const onClose = vi.fn();

      render(<CreateUserDialog {...defaultProps} onClose={onClose} />);

      // Fill form
      fireEvent.change(screen.getByLabelText(/Username/), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByLabelText(/Email/), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/Password/), { target: { value: 'password123' } });

      // Close dialog
      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });

    it('prevents closing when isLoading is true', () => {
      const onClose = vi.fn();

      render(<CreateUserDialog {...defaultProps} isLoading={true} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).not.toHaveBeenCalled();
    });

    it('disables form inputs when isLoading is true', () => {
      render(<CreateUserDialog {...defaultProps} isLoading={true} />);

      expect(screen.getByLabelText(/Username/)).toBeDisabled();
      expect(screen.getByLabelText(/Email/)).toBeDisabled();
      expect(screen.getByLabelText(/Full Name/)).toBeDisabled();
      expect(screen.getByLabelText(/Temporary Password/)).toBeDisabled();
      expect(screen.getByLabelText(/Role/)).toBeDisabled();
    });
  });
});
