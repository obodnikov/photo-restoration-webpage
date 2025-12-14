/**
 * Login form component with sqowe branding.
 */

import { useState, FormEvent } from 'react';
import { useAuth } from '../hooks/useAuth';
import type { LoginCredentials } from '../types';
import '../../../styles/components/auth.css';

export function LoginForm() {
  const { login, isLoading, error } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    const credentials: LoginCredentials = {
      username,
      password,
      rememberMe,
    };

    try {
      await login(credentials);
    } catch (err) {
      // Error is handled by useAuth hook
      console.error('Login failed:', err);
    }
  };

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      {error && (
        <div className="error-message">
          <span className="error-icon"></span>
          <span>{error}</span>
        </div>
      )}

      <div className="form-group">
        <label htmlFor="username" className="form-label">
          Username
        </label>
        <input
          id="username"
          type="text"
          className="form-input"
          placeholder="Enter your username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={isLoading}
          required
          autoComplete="username"
          autoFocus
        />
      </div>

      <div className="form-group">
        <label htmlFor="password" className="form-label">
          Password
        </label>
        <input
          id="password"
          type="password"
          className="form-input"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
          required
          autoComplete="current-password"
        />
      </div>

      <div className="remember-me-group">
        <input
          id="remember-me"
          type="checkbox"
          className="form-checkbox"
          checked={rememberMe}
          onChange={(e) => setRememberMe(e.target.checked)}
          disabled={isLoading}
        />
        <label htmlFor="remember-me" className="checkbox-label">
          Remember me for 7 days
        </label>
      </div>

      <button
        type="submit"
        className="login-button"
        disabled={isLoading || !username || !password}
      >
        <span className="login-button-content">
          {isLoading && <span className="loading-spinner"></span>}
          <span>{isLoading ? 'Signing in...' : 'Sign In'}</span>
        </span>
      </button>
    </form>
  );
}
