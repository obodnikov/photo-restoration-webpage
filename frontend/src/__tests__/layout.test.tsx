import { describe, it, expect, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useAuthStore } from '../services/authStore';

// Mock the auth store
vi.mock('../services/authStore', () => ({
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

describe('Layout Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderLayout = (children: React.ReactNode = <div>Test Content</div>) => {
    return render(
      <BrowserRouter>
        <Layout>{children}</Layout>
      </BrowserRouter>
    );
  };

  describe('Header', () => {
    it('renders sqowe logo', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        clearAuth: vi.fn(),
      } as any);

      renderLayout();
      expect(screen.getByText('sqowe')).toBeInTheDocument();
      expect(screen.getByText('Photo Restoration')).toBeInTheDocument();
    });

    it('renders navigation when authenticated', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        clearAuth: vi.fn(),
      } as any);

      renderLayout();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('History')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
    });

    it('does not render navigation when not authenticated', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        clearAuth: vi.fn(),
      } as any);

      renderLayout();
      expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
      expect(screen.queryByText('Home')).not.toBeInTheDocument();
      expect(screen.queryByText('History')).not.toBeInTheDocument();
    });

    it('highlights active navigation link', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        clearAuth: vi.fn(),
      } as any);

      renderLayout();
      const homeLink = screen.getByRole('link', { name: /home/i });
      expect(homeLink).toHaveClass('active');
    });
  });

  describe('Mobile Navigation', () => {
    it('renders hamburger menu button when authenticated', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        clearAuth: vi.fn(),
      } as any);

      renderLayout();
      const hamburger = screen.getByLabelText('Open menu');
      expect(hamburger).toBeInTheDocument();
    });

    it('toggles mobile menu when hamburger is clicked', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        clearAuth: vi.fn(),
      } as any);

      const user = userEvent.setup();
      renderLayout();

      const hamburger = screen.getByLabelText('Open menu');
      await user.click(hamburger);

      expect(screen.getByLabelText('Close menu')).toBeInTheDocument();
      const nav = screen.getByRole('navigation');
      expect(nav).toHaveClass('mobile-open');
    });

    it('closes mobile menu when navigation link is clicked', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        clearAuth: vi.fn(),
      } as any);

      const user = userEvent.setup();
      renderLayout();

      // Open menu
      const hamburger = screen.getByLabelText('Open menu');
      await user.click(hamburger);

      // Click a nav link
      const homeLink = screen.getByRole('link', { name: /home/i });
      await user.click(homeLink);

      // Menu should close
      const nav = screen.getByRole('navigation');
      expect(nav).not.toHaveClass('mobile-open');
    });
  });

  describe('Logout Functionality', () => {
    it('calls clearAuth and navigates to login on logout', async () => {
      const clearAuth = vi.fn();
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        clearAuth,
      } as any);

      const user = userEvent.setup();
      renderLayout();

      const logoutButton = screen.getByRole('button', { name: /logout/i });
      await user.click(logoutButton);

      expect(clearAuth).toHaveBeenCalledTimes(1);
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  describe('Main Content', () => {
    it('renders children in main section', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        clearAuth: vi.fn(),
      } as any);

      renderLayout(<div>Custom Content</div>);
      expect(screen.getByText('Custom Content')).toBeInTheDocument();
    });
  });

  describe('Footer', () => {
    it('renders copyright text with current year', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        clearAuth: vi.fn(),
      } as any);

      renderLayout();
      const currentYear = new Date().getFullYear();
      expect(screen.getByText(`© ${currentYear} sqowe. All rights reserved.`)).toBeInTheDocument();
    });

    it('renders footer subtitle', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        clearAuth: vi.fn(),
      } as any);

      renderLayout();
      expect(screen.getByText('AI-Powered Photo Restoration')).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('applies correct CSS classes for responsive layout', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        clearAuth: vi.fn(),
      } as any);

      const { container } = renderLayout();
      expect(container.querySelector('.app-layout')).toBeInTheDocument();
      expect(container.querySelector('.app-header')).toBeInTheDocument();
      expect(container.querySelector('.app-main')).toBeInTheDocument();
      expect(container.querySelector('.app-footer')).toBeInTheDocument();
    });
  });
});
