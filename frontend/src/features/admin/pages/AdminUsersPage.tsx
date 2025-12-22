/**
 * Admin Users Page - Main admin panel for user management
 */

import React, { useState } from 'react';
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
import type { AdminUser } from '../types';

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

  // Get current user ID for highlighting
  const currentUserId = users.find((u) => u.username === user?.username)?.id;

  const handleCreateUser = async (userData: any) => {
    setIsCreating(true);
    try {
      await createUser(userData);
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateUser = async (userId: number, userData: any) => {
    setIsUpdating(true);
    try {
      await updateUser(userId, userData);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    setIsDeleting(true);
    try {
      await deleteUser(userId);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleResetPassword = async (userId: number, passwordData: any) => {
    setIsResettingPassword(true);
    try {
      await resetPassword(userId, passwordData);
    } finally {
      setIsResettingPassword(false);
    }
  };

  const handleEdit = (user: AdminUser) => {
    setSelectedUser(user);
    setIsEditDialogOpen(true);
  };

  const handleDelete = (user: AdminUser) => {
    setSelectedUser(user);
    setIsDeleteDialogOpen(true);
  };

  const handleResetPasswordClick = (user: AdminUser) => {
    setSelectedUser(user);
    setIsResetPasswordDialogOpen(true);
  };

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
          onClose={() => setIsCreateDialogOpen(false)}
          onSubmit={handleCreateUser}
          isLoading={isCreating}
        />

        <EditUserDialog
          isOpen={isEditDialogOpen}
          onClose={() => {
            setIsEditDialogOpen(false);
            setSelectedUser(null);
          }}
          onSubmit={handleUpdateUser}
          user={selectedUser}
          isLoading={isUpdating}
        />

        <DeleteUserDialog
          isOpen={isDeleteDialogOpen}
          onClose={() => {
            setIsDeleteDialogOpen(false);
            setSelectedUser(null);
          }}
          onConfirm={handleDeleteUser}
          user={selectedUser}
          isLoading={isDeleting}
        />

        <ResetPasswordDialog
          isOpen={isResetPasswordDialogOpen}
          onClose={() => {
            setIsResetPasswordDialogOpen(false);
            setSelectedUser(null);
          }}
          onSubmit={handleResetPassword}
          user={selectedUser}
          isLoading={isResettingPassword}
        />
      </div>
    </div>
  );
};
