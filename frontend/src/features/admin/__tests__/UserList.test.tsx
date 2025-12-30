import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { UserList } from '../components/UserList';
import type { AdminUser, UserListFilters } from '../types';

describe('UserList', () => {
  const mockUsers: AdminUser[] = [
    {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      full_name: 'Admin User',
      role: 'admin',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      last_login: '2024-12-22T10:00:00Z',
    },
    {
      id: 2,
      username: 'user1',
      email: 'user1@example.com',
      full_name: 'User One',
      role: 'user',
      is_active: true,
      created_at: '2024-01-02T00:00:00Z',
      last_login: '2024-12-21T14:00:00Z',
    },
    {
      id: 3,
      username: 'user2',
      email: 'user2@example.com',
      full_name: 'User Two',
      role: 'user',
      is_active: false,
      created_at: '2024-01-03T00:00:00Z',
      last_login: null,
    },
  ];

  const defaultFilters: UserListFilters = {
    role: null,
    is_active: null,
  };

  const defaultProps = {
    users: mockUsers,
    total: 3,
    currentPage: 1,
    totalPages: 1,
    filters: defaultFilters,
    onPageChange: vi.fn(),
    onFiltersChange: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onResetPassword: vi.fn(),
    currentUserId: 1,
  };

  describe('Rendering', () => {
    it('renders user table with all users', () => {
      render(<UserList {...defaultProps} />);

      expect(screen.getByText('admin')).toBeInTheDocument();
      expect(screen.getByText('user1')).toBeInTheDocument();
      expect(screen.getByText('user2')).toBeInTheDocument();
    });

    it('renders table headers', () => {
      render(<UserList {...defaultProps} />);

      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('Username')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('Full Name')).toBeInTheDocument();
      expect(screen.getByText('Role')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Last Login')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('renders user data in table cells', () => {
      render(<UserList {...defaultProps} />);

      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
      expect(screen.getByText('Admin User')).toBeInTheDocument();
      expect(screen.getByText('User One')).toBeInTheDocument();
      expect(screen.getByText('User Two')).toBeInTheDocument();
    });

    it('displays role badges', () => {
      render(<UserList {...defaultProps} />);

      const adminBadges = screen.getAllByText('Admin');
      const userBadges = screen.getAllByText('User');

      expect(adminBadges.length).toBeGreaterThan(0);
      expect(userBadges.length).toBeGreaterThan(0);
    });

    it('displays status badges (Active/Inactive)', () => {
      render(<UserList {...defaultProps} />);

      const activeBadges = screen.getAllByText('Active');
      const inactiveBadges = screen.getAllByText('Inactive');

      expect(activeBadges).toHaveLength(2); // admin and user1
      expect(inactiveBadges).toHaveLength(1); // user2
    });

    it('highlights current user with "You" badge', () => {
      render(<UserList {...defaultProps} currentUserId={1} />);

      expect(screen.getByText('You')).toBeInTheDocument();
    });

    it('formats last login date correctly', () => {
      render(<UserList {...defaultProps} />);

      // Should format dates as locale string
      const lastLoginCells = screen.getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
      expect(lastLoginCells.length).toBeGreaterThan(0);
    });

    it('displays "Never" for null last login', () => {
      render(<UserList {...defaultProps} />);

      expect(screen.getByText('Never')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no users', () => {
      render(<UserList {...defaultProps} users={[]} total={0} />);

      expect(screen.getByText('No users found')).toBeInTheDocument();
    });

    it('does not display table rows when no users', () => {
      render(<UserList {...defaultProps} users={[]} total={0} />);

      const rows = screen.queryAllByRole('row');
      // Only header row should be present
      expect(rows).toHaveLength(2); // thead row + empty state row
    });
  });

  describe('Filter Controls', () => {
    it('renders role filter dropdown', () => {
      render(<UserList {...defaultProps} />);

      const roleFilter = screen.getByLabelText('Role:');
      expect(roleFilter).toBeInTheDocument();
    });

    it('renders status filter dropdown', () => {
      render(<UserList {...defaultProps} />);

      const statusFilter = screen.getByLabelText('Status:');
      expect(statusFilter).toBeInTheDocument();
    });

    it('role filter has correct options', () => {
      render(<UserList {...defaultProps} />);

      const roleFilter = screen.getByLabelText('Role:') as HTMLSelectElement;
      const options = Array.from(roleFilter.options).map((opt) => opt.value);

      expect(options).toEqual(['', 'admin', 'user']);
    });

    it('status filter has correct options', () => {
      render(<UserList {...defaultProps} />);

      const statusFilter = screen.getByLabelText('Status:') as HTMLSelectElement;
      const options = Array.from(statusFilter.options).map((opt) => opt.value);

      expect(options).toEqual(['', 'true', 'false']);
    });

    it('calls onFiltersChange when role filter changes', () => {
      const onFiltersChange = vi.fn();
      render(<UserList {...defaultProps} onFiltersChange={onFiltersChange} />);

      const roleFilter = screen.getByLabelText('Role:');
      fireEvent.change(roleFilter, { target: { value: 'admin' } });

      expect(onFiltersChange).toHaveBeenCalledWith({
        ...defaultFilters,
        role: 'admin',
      });
    });

    it('calls onFiltersChange when status filter changes', () => {
      const onFiltersChange = vi.fn();
      render(<UserList {...defaultProps} onFiltersChange={onFiltersChange} />);

      const statusFilter = screen.getByLabelText('Status:');
      fireEvent.change(statusFilter, { target: { value: 'true' } });

      expect(onFiltersChange).toHaveBeenCalledWith({
        ...defaultFilters,
        is_active: true,
      });
    });

    it('sets role filter to null when "All" is selected', () => {
      const onFiltersChange = vi.fn();
      const propsWithFilter = {
        ...defaultProps,
        filters: { ...defaultFilters, role: 'admin' as const },
        onFiltersChange,
      };

      render(<UserList {...propsWithFilter} />);

      const roleFilter = screen.getByLabelText('Role:');
      fireEvent.change(roleFilter, { target: { value: '' } });

      expect(onFiltersChange).toHaveBeenCalledWith({
        ...propsWithFilter.filters,
        role: null,
      });
    });

    it('sets status filter to null when "All" is selected', () => {
      const onFiltersChange = vi.fn();
      const propsWithFilter = {
        ...defaultProps,
        filters: { ...defaultFilters, is_active: true },
        onFiltersChange,
      };

      render(<UserList {...propsWithFilter} />);

      const statusFilter = screen.getByLabelText('Status:');
      fireEvent.change(statusFilter, { target: { value: '' } });

      expect(onFiltersChange).toHaveBeenCalledWith({
        ...propsWithFilter.filters,
        is_active: null,
      });
    });
  });

  describe('Action Buttons', () => {
    it('renders Edit button for each user', () => {
      render(<UserList {...defaultProps} />);

      const editButtons = screen.getAllByText('Edit');
      expect(editButtons).toHaveLength(3);
    });

    it('renders Reset Password button for each user', () => {
      render(<UserList {...defaultProps} />);

      const resetButtons = screen.getAllByText('Reset Pwd');
      expect(resetButtons).toHaveLength(3);
    });

    it('renders Delete button for each user', () => {
      render(<UserList {...defaultProps} />);

      const deleteButtons = screen.getAllByText('Delete');
      expect(deleteButtons).toHaveLength(3);
    });

    it('calls onEdit when Edit button is clicked', () => {
      const onEdit = vi.fn();
      render(<UserList {...defaultProps} onEdit={onEdit} />);

      const editButtons = screen.getAllByText('Edit');
      fireEvent.click(editButtons[0]);

      expect(onEdit).toHaveBeenCalledWith(mockUsers[0]);
    });

    it('calls onResetPassword when Reset Password button is clicked', () => {
      const onResetPassword = vi.fn();
      render(<UserList {...defaultProps} onResetPassword={onResetPassword} />);

      const resetButtons = screen.getAllByText('Reset Pwd');
      fireEvent.click(resetButtons[1]);

      expect(onResetPassword).toHaveBeenCalledWith(mockUsers[1]);
    });

    it('calls onDelete when Delete button is clicked', () => {
      const onDelete = vi.fn();
      render(<UserList {...defaultProps} onDelete={onDelete} />);

      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[1]); // Click non-current user

      expect(onDelete).toHaveBeenCalledWith(mockUsers[1]);
    });

    it('disables Delete button for current user', () => {
      render(<UserList {...defaultProps} currentUserId={1} />);

      const deleteButtons = screen.getAllByText('Delete');
      const currentUserDeleteButton = deleteButtons[0];

      expect(currentUserDeleteButton).toBeDisabled();
    });

    it('does not disable Delete button for other users', () => {
      render(<UserList {...defaultProps} currentUserId={1} />);

      const deleteButtons = screen.getAllByText('Delete');
      const otherUserDeleteButton = deleteButtons[1];

      expect(otherUserDeleteButton).not.toBeDisabled();
    });

    it('shows title tooltip on disabled Delete button', () => {
      render(<UserList {...defaultProps} currentUserId={1} />);

      const deleteButtons = screen.getAllByText('Delete');
      const currentUserDeleteButton = deleteButtons[0];

      expect(currentUserDeleteButton).toHaveAttribute(
        'title',
        'Cannot delete your own account'
      );
    });
  });

  describe('Pagination', () => {
    it('does not render pagination when totalPages is 1', () => {
      render(<UserList {...defaultProps} totalPages={1} />);

      expect(screen.queryByText('Previous')).not.toBeInTheDocument();
      expect(screen.queryByText('Next')).not.toBeInTheDocument();
    });

    it('renders pagination when totalPages > 1', () => {
      render(<UserList {...defaultProps} totalPages={3} total={60} />);

      expect(screen.getByText('‹ Previous')).toBeInTheDocument();
      expect(screen.getByText('Next ›')).toBeInTheDocument();
    });

    it('displays pagination info correctly', () => {
      render(<UserList {...defaultProps} currentPage={1} totalPages={3} total={60} />);

      expect(screen.getByText('Showing 1-20 of 60 users')).toBeInTheDocument();
    });

    it('displays correct pagination info for page 2', () => {
      render(<UserList {...defaultProps} currentPage={2} totalPages={3} total={60} />);

      expect(screen.getByText('Showing 21-40 of 60 users')).toBeInTheDocument();
    });

    it('displays correct pagination info for last page', () => {
      render(<UserList {...defaultProps} currentPage={3} totalPages={3} total={45} />);

      expect(screen.getByText('Showing 41-45 of 45 users')).toBeInTheDocument();
    });

    it('calls onPageChange when Previous button is clicked', () => {
      const onPageChange = vi.fn();
      render(
        <UserList
          {...defaultProps}
          currentPage={2}
          totalPages={3}
          total={60}
          onPageChange={onPageChange}
        />
      );

      const prevButton = screen.getByText('‹ Previous');
      fireEvent.click(prevButton);

      expect(onPageChange).toHaveBeenCalledWith(1);
    });

    it('calls onPageChange when Next button is clicked', () => {
      const onPageChange = vi.fn();
      render(
        <UserList
          {...defaultProps}
          currentPage={1}
          totalPages={3}
          total={60}
          onPageChange={onPageChange}
        />
      );

      const nextButton = screen.getByText('Next ›');
      fireEvent.click(nextButton);

      expect(onPageChange).toHaveBeenCalledWith(2);
    });

    it('disables Previous button on first page', () => {
      render(<UserList {...defaultProps} currentPage={1} totalPages={3} total={60} />);

      const prevButton = screen.getByText('‹ Previous');
      expect(prevButton).toBeDisabled();
    });

    it('disables Next button on last page', () => {
      render(<UserList {...defaultProps} currentPage={3} totalPages={3} total={60} />);

      const nextButton = screen.getByText('Next ›');
      expect(nextButton).toBeDisabled();
    });

    it('renders page number buttons', () => {
      render(<UserList {...defaultProps} currentPage={1} totalPages={3} total={60} />);

      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('highlights current page button', () => {
      render(<UserList {...defaultProps} currentPage={2} totalPages={3} total={60} />);

      const pageButtons = screen.getAllByRole('button');
      const page2Button = pageButtons.find(
        (btn) => btn.textContent === '2' && btn.classList.contains('active')
      );

      expect(page2Button).toBeInTheDocument();
    });

    it('calls onPageChange when page number is clicked', () => {
      const onPageChange = vi.fn();
      render(
        <UserList
          {...defaultProps}
          currentPage={1}
          totalPages={3}
          total={60}
          onPageChange={onPageChange}
        />
      );

      const page2Button = screen.getByText('2');
      fireEvent.click(page2Button);

      expect(onPageChange).toHaveBeenCalledWith(2);
    });
  });
});
