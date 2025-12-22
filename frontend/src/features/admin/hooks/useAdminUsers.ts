/**
 * Custom hook for admin user management
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
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

  // Track in-flight deletions to prevent race conditions
  const deletingUsersRef = useRef<Set<number>>(new Set());

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  // Filters - using separate state for each filter value
  const [roleFilter, setRoleFilter] = useState<'admin' | 'user' | null>(null);
  const [isActiveFilter, setIsActiveFilter] = useState<boolean | null>(null);

  // Memoize filters object to prevent unnecessary re-renders
  const filters = useMemo<UserListFilters>(() => ({
    role: roleFilter,
    is_active: isActiveFilter,
  }), [roleFilter, isActiveFilter]);

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
   *
   * Deletes user on backend, then refetches the current page.
   * If the current page becomes empty, navigates to a valid page.
   */
  const deleteUser = useCallback(
    async (userId: number): Promise<void> => {
      setError(null);

      // Prevent concurrent deletions of the same user
      if (deletingUsersRef.current.has(userId)) {
        const message = 'Delete operation already in progress for this user';
        setError(message);
        throw new Error(message);
      }

      // Mark user as being deleted
      deletingUsersRef.current.add(userId);

      try {
        // Perform the delete operation on the backend first
        await adminService.deleteUser(userId);

        // Refetch the current page to get updated data
        const skip = (currentPage - 1) * itemsPerPage;
        const response = await adminService.getUsers(skip, itemsPerPage, filters);

        // Update state with response
        setUsers(response.users);
        setTotal(response.total);

        // If current page is now empty but there are still users, navigate to a valid page
        if (response.users.length === 0 && response.total > 0) {
          const newTotalPages = Math.ceil(response.total / itemsPerPage);
          const validPage = Math.min(currentPage, newTotalPages);
          if (validPage !== currentPage) {
            setCurrentPage(validPage);
          } else if (currentPage > 1) {
            // Edge case: current page is valid but empty, go to previous
            setCurrentPage(currentPage - 1);
          }
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to delete user';
        setError(message);
        console.error(`Failed to delete user ${userId}:`, err);
        throw err;
      } finally {
        deletingUsersRef.current.delete(userId);
      }
    },
    [currentPage, itemsPerPage, filters]
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
    setRoleFilter(newFilters.role ?? null);
    setIsActiveFilter(newFilters.is_active ?? null);
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
