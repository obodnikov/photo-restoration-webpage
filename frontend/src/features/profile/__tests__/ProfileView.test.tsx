import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProfileView } from '../components/ProfileView';
import type { UserProfile } from '../types';

describe('ProfileView', () => {
  const mockProfile: UserProfile = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    full_name: 'Test User',
    role: 'user',
    is_active: true,
    password_must_change: false,
    created_at: '2024-01-01T00:00:00Z',
    last_login: '2024-12-22T10:00:00Z',
  };

  const mockAdminProfile: UserProfile = {
    ...mockProfile,
    role: 'admin',
    username: 'adminuser',
    email: 'admin@example.com',
    full_name: 'Admin User',
  };

  describe('Rendering', () => {
    it('renders profile information correctly', () => {
      render(<ProfileView profile={mockProfile} />);

      expect(screen.getByText('testuser')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    it('renders profile header', () => {
      render(<ProfileView profile={mockProfile} />);

      expect(screen.getByRole('heading', { name: /profile information/i })).toBeInTheDocument();
    });

    it('renders all field labels', () => {
      render(<ProfileView profile={mockProfile} />);

      expect(screen.getByText(/^username$/i)).toBeInTheDocument();
      expect(screen.getByText(/^email$/i)).toBeInTheDocument();
      expect(screen.getByText(/^full name$/i)).toBeInTheDocument();
      expect(screen.getByText(/^account status$/i)).toBeInTheDocument();
      expect(screen.getByText(/member since/i)).toBeInTheDocument();
      expect(screen.getByText(/last login/i)).toBeInTheDocument();
    });
  });

  describe('Role Badge', () => {
    it('displays USER badge for regular users', () => {
      render(<ProfileView profile={mockProfile} />);

      const badge = screen.getByText('USER');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('badge-user');
    });

    it('displays ADMIN badge for admin users', () => {
      render(<ProfileView profile={mockAdminProfile} />);

      const badge = screen.getByText('ADMIN');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('badge-admin');
    });
  });

  describe('Account Status', () => {
    it('displays Active status for active users', () => {
      render(<ProfileView profile={mockProfile} />);

      const status = screen.getByText('Active');
      expect(status).toBeInTheDocument();
      expect(status).toHaveClass('status-badge', 'active');
    });

    it('displays Inactive status for inactive users', () => {
      const inactiveProfile = { ...mockProfile, is_active: false };
      render(<ProfileView profile={inactiveProfile} />);

      const status = screen.getByText('Inactive');
      expect(status).toBeInTheDocument();
      expect(status).toHaveClass('status-badge', 'inactive');
    });
  });

  describe('Date Formatting', () => {
    it('formats member since date correctly', () => {
      render(<ProfileView profile={mockProfile} />);

      // Check that the date is displayed (format depends on locale)
      const memberSinceValue = screen.getByText(/2024/);
      expect(memberSinceValue).toBeInTheDocument();
    });

    it('formats last login date correctly', () => {
      render(<ProfileView profile={mockProfile} />);

      // Check that the date is displayed
      const lastLoginSection = screen.getAllByText(/2024/).filter(
        (el) => el.closest('.profile-field')?.textContent?.includes('Last Login')
      );
      expect(lastLoginSection.length).toBeGreaterThan(0);
    });

    it('displays "Never" for null last login', () => {
      const profileWithoutLogin = { ...mockProfile, last_login: null };
      render(<ProfileView profile={profileWithoutLogin} />);

      expect(screen.getByText('Never')).toBeInTheDocument();
    });
  });

  describe('Data Integrity', () => {
    it('handles long usernames gracefully', () => {
      const longUsernameProfile = {
        ...mockProfile,
        username: 'this_is_a_very_long_username_that_should_not_break_layout',
      };
      render(<ProfileView profile={longUsernameProfile} />);

      expect(screen.getByText(longUsernameProfile.username)).toBeInTheDocument();
    });

    it('handles long email addresses gracefully', () => {
      const longEmailProfile = {
        ...mockProfile,
        email: 'this.is.a.very.long.email.address@verylongdomainname.example.com',
      };
      render(<ProfileView profile={longEmailProfile} />);

      expect(screen.getByText(longEmailProfile.email)).toBeInTheDocument();
    });

    it('handles special characters in full name', () => {
      const specialNameProfile = {
        ...mockProfile,
        full_name: "O'Brien-McDonald, Jr.",
      };
      render(<ProfileView profile={specialNameProfile} />);

      expect(screen.getByText(specialNameProfile.full_name)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses proper semantic HTML', () => {
      const { container } = render(<ProfileView profile={mockProfile} />);

      // Check for proper heading
      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();

      // Check for labels
      const labels = container.querySelectorAll('label');
      expect(labels.length).toBeGreaterThan(0);
    });

    it('has appropriate ARIA structure', () => {
      const { container } = render(<ProfileView profile={mockProfile} />);

      // Check that the component is wrapped in a card
      const card = container.querySelector('.card');
      expect(card).toBeInTheDocument();
    });
  });
});
