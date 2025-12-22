/**
 * Admin Users Page - Main admin panel for user management
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useAuthStore } from '../../../services/authStore';
import { useAdminUsers } from '../hooks/useAdminUsers';
import { UserList } from '../components/UserList';
import { CreateUserDialog } from '../components/CreateUserDialog';
import { EditUserDialog } from '../components/EditUserDialog';
import { DeleteUserDialog } from '../components/DeleteUserDialog';
import { ResetPasswordDialog } from '../components/ResetPasswordDialog';
import { Button } from '../../../components/Button';
import { Loader } from '../../../components/Loader';
import { ErrorMessage } from '../../../components/ErrorMessage';
import type {
  AdminUser,
  CreateUserRequest,
  UpdateUserRequest,
  ResetPasswordRequest,
} from '../types';

export const AdminUsersPage: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const {
    users,
    total,
    isLoading,
    error,
    currentPage,
    totalPages,
    filters,
    createUser,
    updateUser,
    deleteUser,
    resetPassword,
    updateFilters,
    goToPage,
  } = useAdminUsers();

  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isResetPasswordDialogOpen, setIsResetPasswordDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);

  // Loading states for operations
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isResettingPassword, setIsResettingPassword] = useState(false);

  // Memoize current user ID calculation to prevent unnecessary re-renders
  const currentUserId = useMemo(
    () => users.find((u) => u.username === user?.username)?.id,
    [users, user?.username]
  );

  const handleCreateUser = useCallback(async (userData: CreateUserRequest) => {
    setIsCreating(true);
    try {
      await createUser(userData);
    } finally {
      setIsCreating(false);
    }
  }, [createUser]);

  const handleUpdateUser = useCallback(async (userId: number, userData: UpdateUserRequest) => {
    setIsUpdating(true);
    try {
      await updateUser(userId, userData);
    } finally {
      setIsUpdating(false);
    }
  }, [updateUser]);

  const handleDeleteUser = useCallback(async (userId: number) => {
    setIsDeleting(true);
    try {
      await deleteUser(userId);
    } finally {
      setIsDeleting(false);
    }
  }, [deleteUser]);

  const handleResetPassword = useCallback(async (userId: number, passwordData: ResetPasswordRequest) => {
    setIsResettingPassword(true);
    try {
      await resetPassword(userId, passwordData);
    } finally {
      setIsResettingPassword(false);
    }
  }, [resetPassword]);

  const handleEdit = useCallback((user: AdminUser) => {
    setSelectedUser(user);
    setIsEditDialogOpen(true);
  }, []);

  const handleDelete = useCallback((user: AdminUser) => {
    setSelectedUser(user);
    setIsDeleteDialogOpen(true);
  }, []);

  const handleResetPasswordClick = useCallback((user: AdminUser) => {
    setSelectedUser(user);
    setIsResetPasswordDialogOpen(true);
  }, []);

  // Memoize dialog close handlers to prevent unnecessary re-renders
  const handleCloseCreateDialog = useCallback(() => {
    setIsCreateDialogOpen(false);
  }, []);

  const handleCloseEditDialog = useCallback(() => {
    setIsEditDialogOpen(false);
    setSelectedUser(null);
  }, []);

  const handleCloseDeleteDialog = useCallback(() => {
    setIsDeleteDialogOpen(false);
    setSelectedUser(null);
  }, []);

  const handleCloseResetPasswordDialog = useCallback(() => {
    setIsResetPasswordDialogOpen(false);
    setSelectedUser(null);
  }, []);

  return (
    <div className="admin-users-page">
      <div className="container">
        <div className="page-header">
          <div className="page-title-section">
            <h1 className="page-title">User Management</h1>
            <p className="page-subtitle">
              Manage users, roles, and permissions
            </p>
          </div>

          <Button
            variant="primary"
            size="medium"
            onClick={() => setIsCreateDialogOpen(true)}
          >
            + Create User
          </Button>
        </div>

        {error && <ErrorMessage message={error} title="Error Loading Users" />}

        {isLoading && users.length === 0 ? (
          <Loader text="Loading users..." />
        ) : (
          <UserList
            users={users}
            total={total}
            currentPage={currentPage}
            totalPages={totalPages}
            filters={filters}
            onPageChange={goToPage}
            onFiltersChange={updateFilters}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onResetPassword={handleResetPasswordClick}
            currentUserId={currentUserId}
          />
        )}

        {/* Dialogs */}
        <CreateUserDialog
          isOpen={isCreateDialogOpen}
          onClose={handleCloseCreateDialog}
          onSubmit={handleCreateUser}
          isLoading={isCreating}
        />

        <EditUserDialog
          isOpen={isEditDialogOpen}
          onClose={handleCloseEditDialog}
          onSubmit={handleUpdateUser}
          user={selectedUser}
          isLoading={isUpdating}
        />

        <DeleteUserDialog
          isOpen={isDeleteDialogOpen}
          onClose={handleCloseDeleteDialog}
          onConfirm={handleDeleteUser}
          user={selectedUser}
          isLoading={isDeleting}
        />

        <ResetPasswordDialog
          isOpen={isResetPasswordDialogOpen}
          onClose={handleCloseResetPasswordDialog}
          onSubmit={handleResetPassword}
          user={selectedUser}
          isLoading={isResettingPassword}
        />
      </div>
    </div>
  );
};
