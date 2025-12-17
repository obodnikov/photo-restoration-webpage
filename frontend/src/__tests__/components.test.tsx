/**
 * Tests for shared components
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Loader } from '../components/Loader';
import { ErrorMessage } from '../components/ErrorMessage';
import { Layout } from '../components/Layout';

// Mock auth store
vi.mock('../services/authStore', () => ({
  useAuthStore: () => ({
    isAuthenticated: true,
    clearAuth: vi.fn(),
  }),
}));

describe('Button Component', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('renders primary variant by default', () => {
    render(<Button>Primary</Button>);
    const button = screen.getByText('Primary');
    expect(button).toHaveClass('btn-primary');
  });

  it('renders secondary variant', () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByText('Secondary');
    expect(button).toHaveClass('btn-secondary');
  });

  it('renders gradient variant', () => {
    render(<Button variant="gradient">Gradient</Button>);
    const button = screen.getByText('Gradient');
    expect(button).toHaveClass('btn-gradient');
  });

  it('handles onClick event', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('disables button when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByText('Disabled')).toBeDisabled();
  });

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByText('Loading')).toBeInTheDocument();
    expect(screen.getByText('Loading').closest('button')).toBeDisabled();
  });

  it('renders full width button', () => {
    render(<Button fullWidth>Full Width</Button>);
    expect(screen.getByText('Full Width')).toHaveClass('btn-full-width');
  });
});

describe('Card Component', () => {
  it('renders with title', () => {
    render(<Card title="Test Card" />);
    expect(screen.getByText('Test Card')).toBeInTheDocument();
  });

  it('renders with description', () => {
    render(<Card description="Test description" />);
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('renders children', () => {
    render(
      <Card>
        <p>Child content</p>
      </Card>
    );
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('renders dark variant', () => {
    render(<Card variant="dark" title="Dark Card" />);
    const card = screen.getByText('Dark Card').closest('.card');
    expect(card).toHaveClass('card-dark');
  });

  it('handles onClick event', () => {
    const handleClick = vi.fn();
    render(<Card title="Clickable" onClick={handleClick} />);
    fireEvent.click(screen.getByText('Clickable').closest('.card')!);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe('Loader Component', () => {
  it('renders loader', () => {
    const { container } = render(<Loader />);
    expect(container.querySelector('.loader-spinner')).toBeInTheDocument();
  });

  it('renders with text', () => {
    render(<Loader text="Loading..." />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders small size', () => {
    const { container } = render(<Loader size="small" />);
    expect(container.querySelector('.loader-small')).toBeInTheDocument();
  });

  it('renders medium size', () => {
    const { container } = render(<Loader size="medium" />);
    expect(container.querySelector('.loader-medium')).toBeInTheDocument();
  });

  it('renders large size', () => {
    const { container } = render(<Loader size="large" />);
    expect(container.querySelector('.loader-large')).toBeInTheDocument();
  });

  it('renders fullscreen loader', () => {
    const { container } = render(<Loader fullScreen />);
    expect(container.querySelector('.loader-fullscreen')).toBeInTheDocument();
  });
});

describe('ErrorMessage Component', () => {
  it('renders error message', () => {
    render(<ErrorMessage message="Test error" />);
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('renders with custom title', () => {
    render(<ErrorMessage message="Test error" title="Custom Error" />);
    expect(screen.getByText('Custom Error')).toBeInTheDocument();
  });

  it('renders close button when onClose provided', () => {
    const handleClose = vi.fn();
    render(<ErrorMessage message="Test error" onClose={handleClose} />);
    const closeButton = screen.getByLabelText('Close error message');
    expect(closeButton).toBeInTheDocument();
  });

  it('calls onClose when close button clicked', () => {
    const handleClose = vi.fn();
    render(<ErrorMessage message="Test error" onClose={handleClose} />);
    fireEvent.click(screen.getByLabelText('Close error message'));
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});

describe('Layout Component', () => {
  it('renders children', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test content</div>
        </Layout>
      </BrowserRouter>
    );
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('renders header with logo', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Content</div>
        </Layout>
      </BrowserRouter>
    );
    expect(screen.getByText('sqowe')).toBeInTheDocument();
    expect(screen.getByText('Photo Restoration')).toBeInTheDocument();
  });

  it('renders navigation when authenticated', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Content</div>
        </Layout>
      </BrowserRouter>
    );
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('renders footer', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Content</div>
        </Layout>
      </BrowserRouter>
    );
    const currentYear = new Date().getFullYear();
    expect(screen.getByText(`© ${currentYear} sqowe. All rights reserved.`)).toBeInTheDocument();
  });
});
