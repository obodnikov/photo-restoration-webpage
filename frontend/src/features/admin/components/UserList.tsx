/**
 * Props for the UserList component.
 */
export interface UserListProps {
  users: AdminUser[];
  total: number;
  currentPage: number;
  totalPages: number;
  filters: UserListFilters;
  onPageChange: (page: number) => void;
  onFiltersChange: (filters: UserListFilters) => void;
  onEdit: (user: AdminUser) => void;
  onDelete: (user: AdminUser) => void;
  onResetPassword: (user: AdminUser) => void;
  currentUserId?: number;
}

/**
 * UserList - Admin user management table with filtering, pagination, and CRUD actions.
 *
 * Displays users in a table format with role/status filters, pagination controls,
 * and action buttons for editing, password reset, and deletion. Prevents self-deletion
 * and highlights the current user. Supports role-based and status-based filtering.
 *
 * @example
 * ```tsx
 * <UserList
 *   users={users}
 *   total={totalUsers}
 *   currentPage={currentPage}
 *   totalPages={totalPages}
 *   filters={filters}
 *   onPageChange={handlePageChange}
 *   onFiltersChange={handleFiltersChange}
 *   onEdit={handleEditUser}
 *   onDelete={handleDeleteUser}
 *   onResetPassword={handleResetPassword}
 *   currentUserId={currentUser.id}
 * />
 * ```
 *
 * @param props.users - Array of user objects to display.
 * @param props.total - Total number of users across all pages.
 * @param props.currentPage - Current page number (1-based).
 * @param props.totalPages - Total number of pages available.
 * @param props.filters - Current filter settings for role and status.
 * @param props.onPageChange - Callback when page changes.
 * @param props.onFiltersChange - Callback when filters are modified.
 * @param props.onEdit - Callback when edit button is clicked.
 * @param props.onDelete - Callback when delete button is clicked.
 * @param props.onResetPassword - Callback when reset password button is clicked.
 * @param props.currentUserId - ID of current user to prevent self-deletion.
 *
 * @component
 * @category Admin
 */

import React from 'react';
import type { AdminUser, UserListFilters } from '../types';
import { Button } from '../../../components/Button';

export const UserList: React.FC<UserListProps> = ({
  users,
  total,
  currentPage,
  totalPages,
  filters,
  onPageChange,
  onFiltersChange,
  onEdit,
  onDelete,
  onResetPassword,
  currentUserId,
}) => {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const handleRoleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onFiltersChange({
      ...filters,
      role: value === '' ? null : (value as 'admin' | 'user'),
    });
  };

  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onFiltersChange({
      ...filters,
      is_active: value === '' ? null : value === 'true',
    });
  };

  return (
    <div className="user-list">
      {/* Filters */}
      <div className="user-list-filters">
        <div className="filter-group">
          <label htmlFor="role-filter" className="filter-label">
            Role:
          </label>
          <select
            id="role-filter"
            className="filter-select"
            value={filters.role || ''}
            onChange={handleRoleFilterChange}
          >
            <option value="">All</option>
            <option value="admin">Admin</option>
            <option value="user">User</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="status-filter" className="filter-label">
            Status:
          </label>
          <select
            id="status-filter"
            className="filter-select"
            value={filters.is_active === null ? '' : String(filters.is_active)}
            onChange={handleStatusFilterChange}
          >
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        <table className="user-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Full Name</th>
              <th>Role</th>
              <th>Status</th>
              <th>Last Login</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty-state">
                  No users found
                </td>
              </tr>
            ) : (
              users.map((user) => {
                const isCurrentUser = user.id === currentUserId;

                return (
                  <tr key={user.id} className={isCurrentUser ? 'current-user' : ''}>
                    <td>{user.id}</td>
                    <td>
                      {user.username}
                      {isCurrentUser && <span className="badge badge-info">You</span>}
                    </td>
                    <td>{user.email}</td>
                    <td>{user.full_name}</td>
                    <td>
                      <span className={`badge badge-${user.role}`}>
                        {user.role === 'admin' ? 'Admin' : 'User'}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge badge-${user.is_active ? 'success' : 'inactive'}`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="date-cell">{formatDate(user.last_login)}</td>
                    <td className="actions-cell">
                      <div className="action-buttons">
                        <Button
                          variant="secondary"
                          size="small"
                          onClick={() => onEdit(user)}
                          aria-label={`Edit ${user.username}`}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="secondary"
                          size="small"
                          onClick={() => onResetPassword(user)}
                          aria-label={`Reset password for ${user.username}`}
                        >
                          Reset Pwd
                        </Button>
                        <Button
                          variant="danger"
                          size="small"
                          onClick={() => onDelete(user)}
                          disabled={isCurrentUser}
                          aria-label={`Delete ${user.username}`}
                          title={isCurrentUser ? 'Cannot delete your own account' : ''}
                        >
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <div className="pagination-info">
            Showing {(currentPage - 1) * 20 + 1}-
            {Math.min(currentPage * 20, total)} of {total} users
          </div>

          <div className="pagination-controls">
            <Button
              variant="secondary"
              size="small"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              aria-label="Previous page"
            >
              ‹ Previous
            </Button>

            <div className="pagination-pages">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let pageNum: number;

                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }

                return (
                  <button
                    key={pageNum}
                    className={`pagination-page ${
                      currentPage === pageNum ? 'active' : ''
                    }`}
                    onClick={() => onPageChange(pageNum)}
                    aria-label={`Page ${pageNum}`}
                    aria-current={currentPage === pageNum ? 'page' : undefined}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>

            <Button
              variant="secondary"
              size="small"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              aria-label="Next page"
            >
              Next ›
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
