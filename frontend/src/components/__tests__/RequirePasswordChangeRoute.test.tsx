/**
 * RequirePasswordChangeRoute component tests
 * Tests the route guard logic for forced password change page
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { RequirePasswordChangeRoute } from '../RequirePasswordChangeRoute';
import { useAuthStore } from '../../services/authStore';

// Mock dependencies
vi.mock('../../services/authStore', () => ({
  useAuthStore: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    Navigate: ({ to, replace }: { to: string; replace?: boolean }) => {
      mockNavigate(to, replace);
      return <div data-testid="navigate">Redirecting to {to}</div>;
    },
  };
});

// Test child component
const TestChild = () => <div data-testid="test-child">Protected Content</div>;

// Wrapper component for router context
const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('RequirePasswordChangeRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Access Control', () => {
    it('redirects to /login when user is not authenticated', () => {
      vi.mocked(useAuthStore).mockImplementation((selector: any) => {
        const state = {
          isAuthenticated: false,
          user: null,
        };
        return selector ? selector(state) : state;
      });

      renderWithRouter(
        <RequirePasswordChangeRoute>
          <TestChild />
        </RequirePasswordChangeRoute>
      );

      expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
      expect(screen.getByTestId('navigate')).toBeInTheDocument();
      expect(mockNavigate).toHaveBeenCalledWith('/login', true);
    });

    it('redirects to /login when user object is null', () => {
      vi.mocked(useAuthStore).mockImplementation((selector: any) => {
        const state = {
          isAuthenticated: true,
          user: null,
        };
        return selector ? selector(state) : state;
      });

      renderWithRouter(
        <RequirePasswordChangeRoute>
          <TestChild />
        </RequirePasswordChangeRoute>
      );

      expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
      expect(screen.getByTestId('navigate')).toBeInTheDocument();
      expect(mockNavigate).toHaveBeenCalledWith('/login', true);
    });

    it('redirects to / when user does not need password change', () => {
      vi.mocked(useAuthStore).mockImplementation((selector: any) => {
        const state = {
          isAuthenticated: true,
          user: {
            username: 'testuser',
            role: 'user',
            password_must_change: false,
          },
        };
        return selector ? selector(state) : state;
      });

      renderWithRouter(
        <RequirePasswordChangeRoute>
          <TestChild />
        </RequirePasswordChangeRoute>
      );

      expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
      expect(screen.getByTestId('navigate')).toBeInTheDocument();
      expect(mockNavigate).toHaveBeenCalledWith('/', true);
    });

    it('renders children when user needs password change', () => {
      vi.mocked(useAuthStore).mockImplementation((selector: any) => {
        const state = {
          isAuthenticated: true,
          user: {
            username: 'testuser',
            role: 'user',
            password_must_change: true,
          },
        };
        return selector ? selector(state) : state;
      });

      renderWithRouter(
        <RequirePasswordChangeRoute>
          <TestChild />
        </RequirePasswordChangeRoute>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByTestId('navigate')).not.toBeInTheDocument();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Navigation Behavior', () => {
    it('uses replace prop to prevent history entry when redirecting', () => {
      vi.mocked(useAuthStore).mockImplementation((selector: any) => {
        const state = {
          isAuthenticated: false,
          user: null,
        };
        return selector ? selector(state) : state;
      });

      renderWithRouter(
        <RequirePasswordChangeRoute>
          <TestChild />
        </RequirePasswordChangeRoute>
      );

      // Verify replace is true (second argument)
      expect(mockNavigate).toHaveBeenCalledWith('/login', true);
    });

    it('renders children correctly when access is granted', () => {
      vi.mocked(useAuthStore).mockImplementation((selector: any) => {
        const state = {
          isAuthenticated: true,
          user: {
            username: 'adminuser',
            role: 'admin',
            password_must_change: true,
          },
        };
        return selector ? selector(state) : state;
      });

      renderWithRouter(
        <RequirePasswordChangeRoute>
          <TestChild />
        </RequirePasswordChangeRoute>
      );

      // Verify the child component renders with correct content
      const childElement = screen.getByTestId('test-child');
      expect(childElement).toBeInTheDocument();
      expect(childElement).toHaveTextContent('Protected Content');
    });
  });
});
