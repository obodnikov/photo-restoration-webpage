/**
 * Custom hook for admin user management
 */

import { useState, useCallback, useEffect } from 'react';
import * as adminService from '../services/adminService';
import type {
  AdminUser,
  CreateUserRequest,
  UpdateUserRequest,
  ResetPasswordRequest,
  UserListFilters,
} from '../types';

export function useAdminUsers() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  // Filters
  const [filters, setFilters] = useState<UserListFilters>({
    role: null,
    is_active: null,
  });

  /**
   * Fetch users list
   */
  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const skip = (currentPage - 1) * itemsPerPage;
      const response = await adminService.getUsers(skip, itemsPerPage, filters);

      setUsers(response.users);
      setTotal(response.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch users';
      setError(message);
      console.error('Error fetching users:', err);
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, itemsPerPage, filters]);

  /**
   * Create new user
   */
  const createUser = useCallback(async (userData: CreateUserRequest): Promise<void> => {
    setError(null);

    try {
      await adminService.createUser(userData);
      // Refresh the list
      await fetchUsers();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create user';
      setError(message);
      throw err;
    }
  }, [fetchUsers]);

  /**
   * Update user
   */
  const updateUser = useCallback(
    async (userId: number, userData: UpdateUserRequest): Promise<void> => {
      setError(null);

      try {
        const updatedUser = await adminService.updateUser(userId, userData);
        // Update local state
        setUsers((prev) =>
          prev.map((user) => (user.id === userId ? updatedUser : user))
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update user';
        setError(message);
        throw err;
      }
    },
    []
  );

  /**
   * Delete user
   */
  const deleteUser = useCallback(
    async (userId: number): Promise<void> => {
      setError(null);

      try {
        // Calculate new total after deletion
        const newTotal = total - 1;
        const newTotalPages = Math.ceil(newTotal / itemsPerPage);

        // Optimistically remove user and update total
        setUsers((prev) => prev.filter((user) => user.id !== userId));
        setTotal(newTotal);

        // Perform the delete operation
        await adminService.deleteUser(userId);

        // Handle page navigation after successful deletion
        if (newTotal === 0) {
          // No users left, reset to first page
          setCurrentPage(1);
        } else if (currentPage > newTotalPages) {
          // Current page becomes invalid, move to last valid page
          setCurrentPage(newTotalPages);
        } else if (users.length === 1 && currentPage < newTotalPages) {
          // Removed last user on this page but not last page, refetch to show next page users
          // Wrap in try-catch so refresh failures don't appear as delete failures
          try {
            await fetchUsers();
          } catch (refreshErr) {
            // Ignore refresh errors - deletion was successful
            console.warn('Failed to refresh user list after deletion:', refreshErr);
          }
        }
      } catch (err) {
        // Refetch to ensure UI is consistent with server state
        // This handles all edge cases including multiple in-flight deletions
        // Guard the recovery fetch so it doesn't swallow the original error
        try {
          await fetchUsers();
        } catch (fetchErr) {
          // Ignore recovery fetch errors - we want to report the original error
          console.warn('Failed to refresh user list after deletion error:', fetchErr);
        }

        const message = err instanceof Error ? err.message : 'Failed to delete user';
        setError(message);
        throw err;
      }
    },
    [currentPage, total, itemsPerPage, users, fetchUsers]
  );

  /**
   * Reset user password
   */
  const resetPassword = useCallback(
    async (userId: number, passwordData: ResetPasswordRequest): Promise<void> => {
      setError(null);

      try {
        const updatedUser = await adminService.resetUserPassword(userId, passwordData);
        // Update local state
        setUsers((prev) =>
          prev.map((user) => (user.id === userId ? updatedUser : user))
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to reset password';
        setError(message);
        throw err;
      }
    },
    []
  );

  /**
   * Update filters
   */
  const updateFilters = useCallback((newFilters: UserListFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  }, []);

  /**
   * Go to specific page
   */
  const goToPage = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  // Fetch users when dependencies change
  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Calculate total pages
  const totalPages = Math.ceil(total / itemsPerPage);

  return {
    users,
    total,
    isLoading,
    error,
    currentPage,
    totalPages,
    itemsPerPage,
    filters,
    createUser,
    updateUser,
    deleteUser,
    resetPassword,
    updateFilters,
    goToPage,
    refreshUsers: fetchUsers,
  };
}
