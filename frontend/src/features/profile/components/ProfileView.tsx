/**
 * Props for the ProfileView component.
 */
export interface ProfileViewProps {
  profile: UserProfile;
}

/**
 * ProfileView - Displays user profile information in a structured, read-only format.
 *
 * Shows account details including username, email, full name, role, status,
 * creation date, and last login. Includes visual role badges and status indicators.
 *
 * @example
 * ```tsx
 * <ProfileView
 *   profile={userProfile}
 * />
 * ```
 *
 * @param props.profile - User profile object containing account information.
 *
 * @component
 * @category Profile
 */

import React from 'react';
import type { UserProfile } from '../types';
import { Card } from '../../../components/Card';

export const ProfileView: React.FC<ProfileViewProps> = ({ profile }) => {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getRoleBadgeClass = (role: string) => {
    return role === 'admin' ? 'badge badge-admin' : 'badge badge-user';
  };

  return (
    <Card variant="light">
      <div className="profile-view">
        <div className="profile-header">
          <h2>Profile Information</h2>
          <span className={getRoleBadgeClass(profile.role)}>
            {profile.role.toUpperCase()}
          </span>
        </div>

        <div className="profile-info">
          <div className="profile-field">
            <label>Username</label>
            <div className="profile-value">{profile.username}</div>
          </div>

          <div className="profile-field">
            <label>Email</label>
            <div className="profile-value">{profile.email}</div>
          </div>

          <div className="profile-field">
            <label>Full Name</label>
            <div className="profile-value">{profile.full_name}</div>
          </div>

          <div className="profile-field">
            <label>Account Status</label>
            <div className="profile-value">
              <span className={`status-badge ${profile.is_active ? 'active' : 'inactive'}`}>
                {profile.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>

          <div className="profile-field">
            <label>Member Since</label>
            <div className="profile-value">{formatDate(profile.created_at)}</div>
          </div>

          <div className="profile-field">
            <label>Last Login</label>
            <div className="profile-value">{formatDate(profile.last_login)}</div>
          </div>
        </div>
      </div>
    </Card>
  );
};
