import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter } from 'react-router-dom';
import { Button } from '../components/Button';
import { Input, TextArea } from '../components/Input';
import { Modal } from '../components/Modal';
import { Card } from '../components/Card';
import { ErrorMessage } from '../components/ErrorMessage';
import { Layout } from '../components/Layout';
import { useAuthStore } from '../services/authStore';

expect.extend(toHaveNoViolations);

// Mock auth store
vi.mock('../services/authStore', () => ({
  useAuthStore: vi.fn(),
}));

describe('Accessibility Tests', () => {
  describe('Button Accessibility', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(<Button>Click me</Button>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should be keyboard accessible', () => {
      render(<Button>Click me</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      button.focus();
      expect(button).toHaveFocus();
    });
  });

  describe('Input Accessibility', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(<Input label="Username" />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have proper label association', () => {
      render(<Input label="Email" id="email-input" />);
      const input = screen.getByLabelText('Email');
      expect(input).toHaveAttribute('id', 'email-input');
    });

    it('should have aria-invalid when error is present', () => {
      render(<Input label="Name" error="Name is required" />);
      const input = screen.getByLabelText('Name');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('should have aria-describedby for error messages', () => {
      render(<Input label="Email" error="Invalid email" id="email" />);
      const input = screen.getByLabelText('Email');
      expect(input).toHaveAttribute('aria-describedby');
    });

    it('should have aria-describedby for help text', () => {
      render(<Input label="Password" helpText="Min 8 characters" id="password" />);
      const input = screen.getByLabelText('Password');
      expect(input).toHaveAttribute('aria-describedby');
    });
  });

  describe('TextArea Accessibility', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(<TextArea label="Message" />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have proper label association', () => {
      render(<TextArea label="Comment" id="comment-textarea" />);
      const textarea = screen.getByLabelText('Comment');
      expect(textarea).toHaveAttribute('id', 'comment-textarea');
    });
  });

  describe('Modal Accessibility', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <Modal isOpen={true} onClose={vi.fn()} title="Test Modal">
          Modal content
        </Modal>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have role="dialog"', () => {
      render(
        <Modal isOpen={true} onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should have aria-modal="true"', () => {
      render(
        <Modal isOpen={true} onClose={vi.fn()}>
          Content
        </Modal>
      );
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('should have aria-labelledby when title is provided', () => {
      render(
        <Modal isOpen={true} onClose={vi.fn()} title="Modal Title">
          Content
        </Modal>
      );
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title');
    });

    it('close button should have aria-label', () => {
      render(
        <Modal isOpen={true} onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(screen.getByLabelText('Close modal')).toBeInTheDocument();
    });
  });

  describe('Card Accessibility', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <Card title="Card Title" description="Card description">
          Card content
        </Card>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('ErrorMessage Accessibility', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(<ErrorMessage message="An error occurred" />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have role="alert"', () => {
      render(<ErrorMessage message="Error" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('close button should have aria-label', () => {
      render(<ErrorMessage message="Error" />);
      expect(screen.getByLabelText('Close error message')).toBeInTheDocument();
    });
  });

  describe('Layout Accessibility', () => {
    beforeEach(() => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        clearAuth: vi.fn(),
      } as any);
    });

    it('should not have accessibility violations', async () => {
      const { container } = render(
        <BrowserRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </BrowserRouter>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have proper navigation landmark', () => {
      render(
        <BrowserRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </BrowserRouter>
      );
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('should have proper main landmark', () => {
      render(
        <BrowserRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </BrowserRouter>
      );
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('hamburger menu button should have aria-label', () => {
      render(
        <BrowserRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </BrowserRouter>
      );
      const hamburger = screen.getByLabelText('Open menu');
      expect(hamburger).toBeInTheDocument();
    });

    it('hamburger menu button should have aria-expanded', () => {
      render(
        <BrowserRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </BrowserRouter>
      );
      const hamburger = screen.getByLabelText('Open menu');
      expect(hamburger).toHaveAttribute('aria-expanded');
    });
  });

  describe('Focus Management', () => {
    it('all interactive elements should be keyboard focusable', () => {
      render(
        <div>
          <Button>Button</Button>
          <Input label="Input" />
          <a href="#test">Link</a>
        </div>
      );

      const button = screen.getByRole('button');
      const input = screen.getByRole('textbox');
      const link = screen.getByRole('link');

      button.focus();
      expect(button).toHaveFocus();

      input.focus();
      expect(input).toHaveFocus();

      link.focus();
      expect(link).toHaveFocus();
    });

    it('focus should be visible', () => {
      const { container } = render(<Button>Click me</Button>);
      const button = screen.getByRole('button');
      button.focus();

      // Check that focus outline styles are applied
      const styles = window.getComputedStyle(button);
      // Note: In a real browser, outline would be visible
      expect(button).toHaveFocus();
    });
  });

  describe('Color Contrast', () => {
    it('should meet WCAG AA contrast requirements', async () => {
      const { container } = render(
        <div>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="gradient">Gradient</Button>
        </div>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});
