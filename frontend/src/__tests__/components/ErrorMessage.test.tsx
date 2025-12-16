import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ErrorMessage } from '../../components/ErrorMessage';

describe('ErrorMessage Component', () => {
  it('renders error message', () => {
    render(<ErrorMessage message="An error occurred" />);
    expect(screen.getByText('An error occurred')).toBeInTheDocument();
  });

  it('renders with title', () => {
    render(<ErrorMessage message="Error details" title="Error Title" />);
    expect(screen.getByText('Error Title')).toBeInTheDocument();
    expect(screen.getByText('Error details')).toBeInTheDocument();
  });

  it('uses default title "Error" when not provided', () => {
    render(<ErrorMessage message="Something went wrong" />);
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('shows close button by default', () => {
    render(<ErrorMessage message="Error" />);
    expect(screen.getByLabelText('Close error message')).toBeInTheDocument();
  });

  it('hides close button when showClose is false', () => {
    render(<ErrorMessage message="Error" showClose={false} />);
    expect(screen.queryByLabelText('Close error message')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();
    render(<ErrorMessage message="Error" onClose={handleClose} />);

    const closeButton = screen.getByLabelText('Close error message');
    await user.click(closeButton);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('renders as alert role', () => {
    render(<ErrorMessage message="Error" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<ErrorMessage message="Error" className="custom-error" />);
    const errorDiv = container.querySelector('.error-message');
    expect(errorDiv).toHaveClass('custom-error');
  });
});
