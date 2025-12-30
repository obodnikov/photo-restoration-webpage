import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useAdminUsers } from '../hooks/useAdminUsers';
import * as adminService from '../services/adminService';
import type {
  AdminUser,
  CreateUserRequest,
  UpdateUserRequest,
  ResetPasswordRequest,
  UserListResponse,
} from '../types';

// Mock the admin service
vi.mock('../services/adminService', () => ({
  getUsers: vi.fn(),
  getUser: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
  resetUserPassword: vi.fn(),
  generateRandomPassword: vi.fn(),
}));

describe('useAdminUsers', () => {
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

  const mockUserListResponse: UserListResponse = {
    users: mockUsers,
    total: 3,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(adminService.getUsers).mockResolvedValue(mockUserListResponse);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Initial State', () => {
    it('initializes with correct default state', async () => {
      const { result } = renderHook(() => useAdminUsers());

      // Initial state
      expect(result.current.users).toEqual([]);
      expect(result.current.total).toBe(0);
      expect(result.current.error).toBeNull();
      expect(result.current.currentPage).toBe(1);
      expect(result.current.itemsPerPage).toBe(20);
      expect(result.current.filters).toEqual({ role: null, is_active: null });

      // Wait for loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('loads users on mount', async () => {
      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
        expect(result.current.total).toBe(3);
      });

      expect(adminService.getUsers).toHaveBeenCalledWith(0, 20, {
        role: null,
        is_active: null,
      });
    });
  });

  describe('User List Fetching', () => {
    it('fetches users with pagination', async () => {
      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      // Go to page 2
      result.current.goToPage(2);

      await waitFor(() => {
        expect(adminService.getUsers).toHaveBeenCalledWith(20, 20, {
          role: null,
          is_active: null,
        });
      });
    });

    it('sets loading state while fetching users', async () => {
      let resolveUsers: (value: UserListResponse) => void;
      const usersPromise = new Promise<UserListResponse>((resolve) => {
        resolveUsers = resolve;
      });
      vi.mocked(adminService.getUsers).mockReturnValue(usersPromise);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });

      resolveUsers!(mockUserListResponse);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('handles error when fetch fails', async () => {
      const error = new Error('Failed to fetch users');
      vi.mocked(adminService.getUsers).mockRejectedValue(error);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to fetch users');
        expect(result.current.users).toEqual([]);
      });
    });

    it('applies role filter (admin)', async () => {
      const adminUsers = [mockUsers[0]];
      vi.mocked(adminService.getUsers).mockResolvedValue({
        users: adminUsers,
        total: 1,
      });

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      result.current.updateFilters({ role: 'admin' });

      await waitFor(() => {
        expect(adminService.getUsers).toHaveBeenCalledWith(0, 20, {
          role: 'admin',
          is_active: null,
        });
        expect(result.current.users).toEqual(adminUsers);
        expect(result.current.total).toBe(1);
      });
    });

    it('applies role filter (user)', async () => {
      const regularUsers = [mockUsers[1], mockUsers[2]];
      vi.mocked(adminService.getUsers).mockResolvedValue({
        users: regularUsers,
        total: 2,
      });

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      result.current.updateFilters({ role: 'user' });

      await waitFor(() => {
        expect(adminService.getUsers).toHaveBeenCalledWith(0, 20, {
          role: 'user',
          is_active: null,
        });
        expect(result.current.users).toEqual(regularUsers);
        expect(result.current.total).toBe(2);
      });
    });

    it('applies status filter (active)', async () => {
      const activeUsers = [mockUsers[0], mockUsers[1]];
      vi.mocked(adminService.getUsers).mockResolvedValue({
        users: activeUsers,
        total: 2,
      });

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      result.current.updateFilters({ is_active: true });

      await waitFor(() => {
        expect(adminService.getUsers).toHaveBeenCalledWith(0, 20, {
          role: null,
          is_active: true,
        });
        expect(result.current.users).toEqual(activeUsers);
        expect(result.current.total).toBe(2);
      });
    });

    it('applies status filter (inactive)', async () => {
      const inactiveUsers = [mockUsers[2]];
      vi.mocked(adminService.getUsers).mockResolvedValue({
        users: inactiveUsers,
        total: 1,
      });

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      result.current.updateFilters({ is_active: false });

      await waitFor(() => {
        expect(adminService.getUsers).toHaveBeenCalledWith(0, 20, {
          role: null,
          is_active: false,
        });
        expect(result.current.users).toEqual(inactiveUsers);
        expect(result.current.total).toBe(1);
      });
    });

    it('applies combined filters (role + status)', async () => {
      const filteredUsers = [mockUsers[1]];
      vi.mocked(adminService.getUsers).mockResolvedValue({
        users: filteredUsers,
        total: 1,
      });

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      result.current.updateFilters({ role: 'user', is_active: true });

      await waitFor(() => {
        expect(adminService.getUsers).toHaveBeenCalledWith(0, 20, {
          role: 'user',
          is_active: true,
        });
        expect(result.current.users).toEqual(filteredUsers);
        expect(result.current.total).toBe(1);
      });
    });
  });

  describe('Create User', () => {
    it('creates a new user and refreshes the list', async () => {
      const newUser: CreateUserRequest = {
        username: 'newuser',
        email: 'newuser@example.com',
        full_name: 'New User',
        password: 'SecurePass123!',
        role: 'user',
        password_must_change: true,
      };

      const createdUser: AdminUser = {
        id: 4,
        username: newUser.username,
        email: newUser.email,
        full_name: newUser.full_name,
        role: newUser.role,
        is_active: true,
        created_at: '2024-12-22T12:00:00Z',
        last_login: null,
      };

      vi.mocked(adminService.createUser).mockResolvedValue(createdUser);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await result.current.createUser(newUser);

      await waitFor(() => {
        expect(adminService.createUser).toHaveBeenCalledWith(newUser);
        expect(adminService.getUsers).toHaveBeenCalledTimes(2); // Initial load + refresh after create
      });
    });

    it('handles error when create fails (duplicate username)', async () => {
      const newUser: CreateUserRequest = {
        username: 'admin',
        email: 'admin2@example.com',
        full_name: 'Admin Two',
        password: 'SecurePass123!',
        role: 'admin',
        password_must_change: false,
      };

      const error = new Error('Username already exists');
      vi.mocked(adminService.createUser).mockRejectedValue(error);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await expect(result.current.createUser(newUser)).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe('Username already exists');
      });
    });
  });

  describe('Update User', () => {
    it('updates a user and updates local state', async () => {
      const updateData: UpdateUserRequest = {
        full_name: 'Updated User Name',
        email: 'updated@example.com',
      };

      const updatedUser: AdminUser = {
        ...mockUsers[1],
        full_name: updateData.full_name!,
        email: updateData.email!,
      };

      vi.mocked(adminService.updateUser).mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await result.current.updateUser(2, updateData);

      await waitFor(() => {
        expect(adminService.updateUser).toHaveBeenCalledWith(2, updateData);
        expect(result.current.users[1]).toEqual(updatedUser);
      });
    });

    it('updates user role', async () => {
      const updateData: UpdateUserRequest = {
        role: 'admin',
      };

      const updatedUser: AdminUser = {
        ...mockUsers[1],
        role: 'admin',
      };

      vi.mocked(adminService.updateUser).mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await result.current.updateUser(2, updateData);

      await waitFor(() => {
        expect(adminService.updateUser).toHaveBeenCalledWith(2, updateData);
        expect(result.current.users[1].role).toBe('admin');
      });
    });

    it('toggles user active status', async () => {
      const updateData: UpdateUserRequest = {
        is_active: false,
      };

      const updatedUser: AdminUser = {
        ...mockUsers[1],
        is_active: false,
      };

      vi.mocked(adminService.updateUser).mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await result.current.updateUser(2, updateData);

      await waitFor(() => {
        expect(adminService.updateUser).toHaveBeenCalledWith(2, updateData);
        expect(result.current.users[1].is_active).toBe(false);
      });
    });

    it('handles error when update fails', async () => {
      const error = new Error('Update failed');
      vi.mocked(adminService.updateUser).mockRejectedValue(error);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await expect(result.current.updateUser(2, {})).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe('Update failed');
      });
    });
  });

  describe('Delete User', () => {
    it('deletes a user and refreshes the list', async () => {
      vi.mocked(adminService.deleteUser).mockResolvedValue();
      vi.mocked(adminService.getUsers).mockResolvedValue({
        users: [mockUsers[0], mockUsers[2]],
        total: 2,
      });

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await result.current.deleteUser(2);

      await waitFor(() => {
        expect(adminService.deleteUser).toHaveBeenCalledWith(2);
        expect(result.current.users).toEqual([mockUsers[0], mockUsers[2]]);
        expect(result.current.total).toBe(2);
      });
    });

    it('handles error when delete fails', async () => {
      const error = new Error('Delete failed');
      vi.mocked(adminService.deleteUser).mockRejectedValue(error);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await expect(result.current.deleteUser(2)).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe('Delete failed');
      });
    });

    it('prevents concurrent deletions of the same user', async () => {
      // Make delete operation slow to test concurrency
      let resolveDelete: () => void;
      const deletePromise = new Promise<void>((resolve) => {
        resolveDelete = resolve;
      });
      vi.mocked(adminService.deleteUser).mockReturnValue(deletePromise);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      // Start first deletion
      const firstDelete = result.current.deleteUser(2);

      // Try to delete same user again before first completes
      await expect(result.current.deleteUser(2)).rejects.toThrow(
        'Delete operation already in progress for this user'
      );

      // Complete first deletion
      resolveDelete!();
      await firstDelete;
    });

    it('navigates to valid page when current page becomes empty after deletion', async () => {
      // Setup: user on page 2 with only 1 item
      vi.mocked(adminService.getUsers)
        .mockResolvedValueOnce({
          users: [mockUsers[1]],
          total: 21,
        })
        .mockResolvedValueOnce({
          users: [],
          total: 20,
        });

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      // Go to page 2
      result.current.goToPage(2);

      await waitFor(() => {
        expect(result.current.currentPage).toBe(2);
      });

      // Delete the only user on page 2
      vi.mocked(adminService.deleteUser).mockResolvedValue();

      await result.current.deleteUser(2);

      // Should navigate back to page 1
      await waitFor(() => {
        expect(result.current.currentPage).toBe(1);
      });
    });
  });

  describe('Reset Password', () => {
    it('resets user password successfully', async () => {
      const passwordData: ResetPasswordRequest = {
        new_password: 'NewSecurePass123!',
        password_must_change: true,
      };

      const updatedUser: AdminUser = {
        ...mockUsers[1],
      };

      vi.mocked(adminService.resetUserPassword).mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await result.current.resetPassword(2, passwordData);

      await waitFor(() => {
        expect(adminService.resetUserPassword).toHaveBeenCalledWith(2, passwordData);
        expect(result.current.users[1]).toEqual(updatedUser);
      });
    });

    it('handles error when reset password fails', async () => {
      const passwordData: ResetPasswordRequest = {
        new_password: 'weak',
        password_must_change: false,
      };

      const error = new Error('Password does not meet requirements');
      vi.mocked(adminService.resetUserPassword).mockRejectedValue(error);

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      await expect(result.current.resetPassword(2, passwordData)).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe('Password does not meet requirements');
      });
    });
  });

  describe('Pagination', () => {
    it('changes page correctly', async () => {
      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      result.current.goToPage(2);

      await waitFor(() => {
        expect(result.current.currentPage).toBe(2);
        expect(adminService.getUsers).toHaveBeenCalledWith(20, 20, {
          role: null,
          is_active: null,
        });
      });
    });

    it('calculates total pages correctly', async () => {
      vi.mocked(adminService.getUsers).mockResolvedValue({
        users: mockUsers,
        total: 45,
      });

      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.totalPages).toBe(3); // 45 / 20 = 2.25 -> ceil = 3
      });
    });

    it('resets to page 1 when filters change', async () => {
      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
      });

      // Go to page 2
      result.current.goToPage(2);

      await waitFor(() => {
        expect(result.current.currentPage).toBe(2);
      });

      // Change filter
      result.current.updateFilters({ role: 'admin' });

      await waitFor(() => {
        expect(result.current.currentPage).toBe(1);
      });
    });
  });

  describe('Refresh Users', () => {
    it('refreshes user list on demand', async () => {
      const { result } = renderHook(() => useAdminUsers());

      await waitFor(() => {
        expect(result.current.users).toEqual(mockUsers);
        expect(adminService.getUsers).toHaveBeenCalledTimes(1);
      });

      await result.current.refreshUsers();

      await waitFor(() => {
        expect(adminService.getUsers).toHaveBeenCalledTimes(2);
      });
    });
  });
});
