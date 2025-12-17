/**
 * Layout component with Header and Footer
 * Provides consistent layout across all pages with mobile hamburger menu
 */

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../services/authStore';

export interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, clearAuth } = useAuthStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    clearAuth();
    navigate('/login');
    setIsMobileMenuOpen(false);
  };

  const isActivePath = (path: string) => location.pathname === path;

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="container">
          <div className="header-content">
            <Link to="/" className="header-logo" onClick={closeMobileMenu}>
              <span className="logo-text">sqowe</span>
              <span className="logo-subtitle">Photo Restoration</span>
            </Link>

            {isAuthenticated && (
              <>
                <button
                  className="mobile-menu-toggle"
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
                  aria-expanded={isMobileMenuOpen}
                >
                  <span className={`hamburger ${isMobileMenuOpen ? 'active' : ''}`}>
                    <span></span>
                    <span></span>
                    <span></span>
                  </span>
                </button>

                <nav className={`header-nav ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
                  <Link
                    to="/"
                    className={`nav-link ${isActivePath('/') ? 'active' : ''}`}
                    onClick={closeMobileMenu}
                  >
                    Home
                  </Link>
                  <Link
                    to="/history"
                    className={`nav-link ${isActivePath('/history') ? 'active' : ''}`}
                    onClick={closeMobileMenu}
                  >
                    History
                  </Link>
                  <button onClick={handleLogout} className="btn btn-secondary btn-small">
                    Logout
                  </button>
                </nav>
              </>
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
