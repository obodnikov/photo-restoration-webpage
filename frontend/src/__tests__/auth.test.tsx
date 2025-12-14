/**
 * Tests for authentication components and hooks
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderWithRouter, screen, waitFor, userEvent } from '../test-utils';
import { LoginForm } from '../features/auth/components/LoginForm';
import { useAuth } from '../features/auth/hooks/useAuth';
import { useAuthStore } from '../services/authStore';
import * as authService from '../features/auth/services/authService';
import {
  mockLoginResponse,
  mockLoginResponseRememberMe,
  mockToken,
  mockUser,
} from '../test-utils';

// Mock react-router-dom's navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    BrowserRouter: ({ children }: { children: React.ReactNode }) => children,
  };
});

describe('LoginForm Component', () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  it('should render username and password fields', () => {
    renderWithRouter(<LoginForm />);

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('should render Remember Me checkbox', () => {
    renderWithRouter(<LoginForm />);

    const checkbox = screen.getByRole('checkbox', { name: /remember me/i });
    expect(checkbox).toBeInTheDocument();
  });

  it('should have Sign In button disabled when fields are empty', () => {
    renderWithRouter(<LoginForm />);

    const button = screen.getByRole('button', { name: /sign in/i });
    expect(button).toBeDisabled();
  });

  it('should enable Sign In button when both fields are filled', async () => {
    renderWithRouter(<LoginForm />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const button = screen.getByRole('button', { name: /sign in/i });

    // Type in the fields
    await userEvent.type(usernameInput, 'testuser');
    await userEvent.type(passwordInput, 'password123');

    await waitFor(() => {
      expect(button).not.toBeDisabled();
    });
  });

  it('should show error message on invalid credentials', async () => {
    // Mock login API to return error
    vi.spyOn(authService, 'login').mockRejectedValueOnce(
      new Error('Invalid credentials')
    );

    renderWithRouter(<LoginForm />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const button = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(usernameInput, 'wronguser');
    await userEvent.type(passwordInput, 'wrongpass');
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('should show loading state during login', async () => {
    // Mock a slow login
    vi.spyOn(authService, 'login').mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          setTimeout(() => resolve(mockLoginResponse), 100);
        })
    );

    renderWithRouter(<LoginForm />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const button = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(usernameInput, 'testuser');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.click(button);

    // Should show loading text
    expect(screen.getByText(/signing in/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText(/signing in/i)).not.toBeInTheDocument();
    });
  });

  it('should submit with valid credentials and store token', async () => {
    vi.spyOn(authService, 'login').mockResolvedValueOnce(mockLoginResponse);

    renderWithRouter(<LoginForm />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const button = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(usernameInput, 'testuser');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.click(button);

    await waitFor(() => {
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe(mockLoginResponse.access_token);
    });
  });

  it('should redirect to home after successful login', async () => {
    vi.spyOn(authService, 'login').mockResolvedValueOnce(mockLoginResponse);

    renderWithRouter(<LoginForm />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const button = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(usernameInput, 'testuser');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.click(button);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });

  it('should send remember_me: true when checkbox is checked', async () => {
    const loginSpy = vi
      .spyOn(authService, 'login')
      .mockResolvedValueOnce(mockLoginResponseRememberMe);

    renderWithRouter(<LoginForm />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const rememberCheckbox = screen.getByRole('checkbox', {
      name: /remember me/i,
    });
    const button = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(usernameInput, 'testuser');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.click(rememberCheckbox);
    await userEvent.click(button);

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
        rememberMe: true,
      });
    });
  });

  it('should send remember_me: false when checkbox is not checked', async () => {
    const loginSpy = vi
      .spyOn(authService, 'login')
      .mockResolvedValueOnce(mockLoginResponse);

    renderWithRouter(<LoginForm />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const button = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(usernameInput, 'testuser');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.click(button);

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
        rememberMe: false,
      });
    });
  });
});

// Test helper component for useAuth hook
function UseAuthTestComponent() {
  const { isAuthenticated, user, login, logout, isLoading, error } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      {user && <div data-testid="username">{user.username}</div>}
      {isLoading && <div data-testid="loading">Loading</div>}
      {error && <div data-testid="error">{error}</div>}
      <button
        data-testid="login-button"
        onClick={() =>
          login({ username: 'testuser', password: 'testpass', rememberMe: false })
        }
      >
        Login
      </button>
      <button data-testid="logout-button" onClick={logout}>
        Logout
      </button>
    </div>
  );
}

describe('useAuth Hook', () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  it('should provide isAuthenticated as false initially', () => {
    renderWithRouter(<UseAuthTestComponent />);

    expect(screen.getByTestId('auth-status')).toHaveTextContent(
      'Not Authenticated'
    );
  });

  it('should update isAuthenticated after successful login', async () => {
    vi.spyOn(authService, 'login').mockResolvedValueOnce(mockLoginResponse);

    renderWithRouter(<UseAuthTestComponent />);

    const loginButton = screen.getByTestId('login-button');
    await userEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent(
        'Authenticated'
      );
    });
  });

  it('should store token after login', async () => {
    vi.spyOn(authService, 'login').mockResolvedValueOnce(mockLoginResponse);

    renderWithRouter(<UseAuthTestComponent />);

    const loginButton = screen.getByTestId('login-button');
    await userEvent.click(loginButton);

    await waitFor(() => {
      const state = useAuthStore.getState();
      expect(state.token).toBe(mockLoginResponse.access_token);
    });
  });

  it('should clear token on logout', async () => {
    // First login
    useAuthStore.getState().setAuth(mockToken, 86400, mockUser);

    renderWithRouter(<UseAuthTestComponent />);

    expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');

    const logoutButton = screen.getByTestId('logout-button');
    await userEvent.click(logoutButton);

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent(
        'Not Authenticated'
      );
      expect(useAuthStore.getState().token).toBe(null);
    });
  });

  it('should navigate to login page on logout', async () => {
    useAuthStore.getState().setAuth(mockToken, 86400, mockUser);

    renderWithRouter(<UseAuthTestComponent />);

    const logoutButton = screen.getByTestId('logout-button');
    await userEvent.click(logoutButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('should show error when login fails', async () => {
    vi.spyOn(authService, 'login').mockRejectedValueOnce(
      new Error('Invalid credentials')
    );

    renderWithRouter(<UseAuthTestComponent />);

    const loginButton = screen.getByTestId('login-button');
    await userEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent(
        'Invalid credentials'
      );
    });
  });

  it('should show loading state during login', async () => {
    vi.spyOn(authService, 'login').mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          setTimeout(() => resolve(mockLoginResponse), 100);
        })
    );

    renderWithRouter(<UseAuthTestComponent />);

    const loginButton = screen.getByTestId('login-button');
    await userEvent.click(loginButton);

    // Should show loading
    expect(screen.getByTestId('loading')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
    });
  });
});
