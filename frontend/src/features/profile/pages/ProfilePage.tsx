/**
 * ProfilePage - main profile page component
 */

import React from 'react';
import { useProfile } from '../hooks/useProfile';
import { ProfileView } from '../components/ProfileView';
import { ChangePasswordForm } from '../components/ChangePasswordForm';
import { SessionsList } from '../components/SessionsList';
import { Loader } from '../../../components/Loader';
import { ErrorMessage } from '../../../components/ErrorMessage';

export const ProfilePage: React.FC = () => {
  const {
    profile,
    sessions,
    isLoadingProfile,
    isLoadingSessions,
    isChangingPassword,
    profileError,
    sessionsError,
    mutationError,
    changePassword,
    deleteSession,
  } = useProfile();

  // Show loader while initial profile data is loading
  if (isLoadingProfile && !profile) {
    return (
      <div className="profile-page">
        <div className="container">
          <Loader size="large" text="Loading profile..." fullScreen />
        </div>
      </div>
    );
  }

  // Show error if initial profile fetch failed (no data available yet)
  // Note: This handles the case where profile has never been successfully loaded
  if (profileError && !profile) {
    return (
      <div className="profile-page">
        <div className="container">
          <ErrorMessage
            message={profileError}
            title="Failed to Load Profile"
          />
        </div>
      </div>
    );
  }

  // Profile should be loaded at this point
  if (!profile) {
    return null;
  }

  return (
    <div className="profile-page">
      <div className="container">
        <div className="page-header">
          <h1>My Profile</h1>
          <p className="page-description">
            Manage your account settings, password, and active sessions
          </p>
        </div>

        {/* Show profile refresh errors
            Note: This handles subsequent fetchProfile() failures after initial load.
            When a refresh fails, profileError is set but profile retains stale data.
            This ensures users see the error even when stale profile data is displayed.
        */}
        {profileError && profile && (
          <ErrorMessage
            message={profileError}
            title="Failed to Refresh Profile"
          />
        )}

        {/* Show mutation errors (password change, session deletion) */}
        {mutationError && (
          <ErrorMessage message={mutationError} />
        )}

        <div className="profile-grid">
          {/* Profile Information */}
          <div className="profile-section">
            <ProfileView profile={profile} />
          </div>

          {/* Change Password */}
          <div className="profile-section">
            <ChangePasswordForm
              onSubmit={changePassword}
              isLoading={isChangingPassword}
            />
          </div>

          {/* Active Sessions */}
          <div className="profile-section profile-section-full">
            {isLoadingSessions && !sessions.length ? (
              <Loader text="Loading sessions..." />
            ) : (
              <SessionsList
                sessions={sessions}
                onDeleteSession={deleteSession}
                isLoading={isLoadingSessions}
                error={sessionsError}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
