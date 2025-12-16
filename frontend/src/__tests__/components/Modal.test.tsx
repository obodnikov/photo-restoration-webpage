import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Modal } from '../../components/Modal';

describe('Modal Component', () => {
  beforeEach(() => {
    // Create a div for portal
    const portalRoot = document.createElement('div');
    portalRoot.setAttribute('id', 'portal-root');
    document.body.appendChild(portalRoot);
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('does not render when isOpen is false', () => {
    render(<Modal isOpen={false} onClose={vi.fn()}>Content</Modal>);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders when isOpen is true', () => {
    render(<Modal isOpen={true} onClose={vi.fn()}>Content</Modal>);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('renders with title', () => {
    render(<Modal isOpen={true} onClose={vi.fn()} title="Modal Title">Content</Modal>);
    expect(screen.getByText('Modal Title')).toBeInTheDocument();
  });

  it('renders children in modal body', () => {
    render(<Modal isOpen={true} onClose={vi.fn()}>Modal Content</Modal>);
    expect(screen.getByText('Modal Content')).toBeInTheDocument();
  });

  it('renders footer when provided', () => {
    const footer = <button>Footer Button</button>;
    render(<Modal isOpen={true} onClose={vi.fn()} footer={footer}>Content</Modal>);
    expect(screen.getByText('Footer Button')).toBeInTheDocument();
  });

  it('shows close button by default', () => {
    render(<Modal isOpen={true} onClose={vi.fn()}>Content</Modal>);
    expect(screen.getByLabelText('Close modal')).toBeInTheDocument();
  });

  it('hides close button when showCloseButton is false', () => {
    render(<Modal isOpen={true} onClose={vi.fn()} showCloseButton={false}>Content</Modal>);
    expect(screen.queryByLabelText('Close modal')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();
    render(<Modal isOpen={true} onClose={handleClose}>Content</Modal>);

    const closeButton = screen.getByLabelText('Close modal');
    await user.click(closeButton);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when overlay is clicked and closeOnOverlayClick is true', async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();
    render(<Modal isOpen={true} onClose={handleClose} closeOnOverlayClick={true}>Content</Modal>);

    const overlay = screen.getByRole('dialog');
    await user.click(overlay);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('does not call onClose when overlay is clicked and closeOnOverlayClick is false', async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();
    render(<Modal isOpen={true} onClose={handleClose} closeOnOverlayClick={false}>Content</Modal>);

    const overlay = screen.getByRole('dialog');
    await user.click(overlay);

    expect(handleClose).not.toHaveBeenCalled();
  });

  it('does not call onClose when modal content is clicked', async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();
    render(<Modal isOpen={true} onClose={handleClose}>Modal Content</Modal>);

    const content = screen.getByText('Modal Content');
    await user.click(content);

    expect(handleClose).not.toHaveBeenCalled();
  });

  it('calls onClose when Escape key is pressed and closeOnEscape is true', async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();
    render(<Modal isOpen={true} onClose={handleClose} closeOnEscape={true}>Content</Modal>);

    await user.keyboard('{Escape}');

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('does not call onClose when Escape key is pressed and closeOnEscape is false', async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();
    render(<Modal isOpen={true} onClose={handleClose} closeOnEscape={false}>Content</Modal>);

    await user.keyboard('{Escape}');

    expect(handleClose).not.toHaveBeenCalled();
  });

  it('sets aria-modal attribute', () => {
    render(<Modal isOpen={true} onClose={vi.fn()}>Content</Modal>);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('sets aria-labelledby when title is provided', () => {
    render(<Modal isOpen={true} onClose={vi.fn()} title="Modal Title">Content</Modal>);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title');
  });

  it('prevents body scroll when open', () => {
    render(<Modal isOpen={true} onClose={vi.fn()}>Content</Modal>);
    expect(document.body.style.overflow).toBe('hidden');
  });
});
