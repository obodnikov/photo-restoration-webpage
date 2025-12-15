/**
 * Layout component with Header and Footer
 * Provides consistent layout across all pages
 */

import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../services/authStore';

export interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, clearAuth } = useAuthStore();

  const handleLogout = () => {
    clearAuth();
    navigate('/login');
  };

  const isActivePath = (path: string) => location.pathname === path;

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="container">
          <div className="header-content">
            <Link to="/" className="header-logo">
              <span className="logo-text">sqowe</span>
              <span className="logo-subtitle">Photo Restoration</span>
            </Link>

            {isAuthenticated && (
              <nav className="header-nav">
                <Link
                  to="/"
                  className={`nav-link ${isActivePath('/') ? 'active' : ''}`}
                >
                  Home
                </Link>
                <Link
                  to="/history"
                  className={`nav-link ${isActivePath('/history') ? 'active' : ''}`}
                >
                  History
                </Link>
                <button onClick={handleLogout} className="btn btn-secondary btn-small">
                  Logout
                </button>
              </nav>
            )}
          </div>
        </div>
      </header>

      <main className="app-main">
        {children}
      </main>

      <footer className="app-footer">
        <div className="container">
          <div className="footer-content">
            <p className="footer-text">
              &copy; {new Date().getFullYear()} sqowe. All rights reserved.
            </p>
            <p className="footer-subtitle">
              AI-Powered Photo Restoration
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
