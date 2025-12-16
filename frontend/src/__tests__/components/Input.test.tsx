import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input, TextArea } from '../../components/Input';

describe('Input Component', () => {
  it('renders input field', () => {
    render(<Input />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<Input label="Username" />);
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
  });

  it('shows required asterisk when required', () => {
    render(<Input label="Email" required />);
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('renders with help text', () => {
    render(<Input helpText="Enter your email address" />);
    expect(screen.getByText('Enter your email address')).toBeInTheDocument();
  });

  it('renders with error message', () => {
    render(<Input error="This field is required" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('This field is required')).toBeInTheDocument();
  });

  it('applies error class when error is present', () => {
    render(<Input error="Error" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('form-input-error');
  });

  it('hides help text when error is shown', () => {
    render(<Input helpText="Help text" error="Error" />);
    expect(screen.queryByText('Help text')).not.toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('handles value changes', async () => {
    const user = userEvent.setup();
    render(<Input />);
    const input = screen.getByRole('textbox');

    await user.type(input, 'test value');
    expect(input).toHaveValue('test value');
  });

  it('forwards type prop', () => {
    render(<Input type="email" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'email');
  });

  it('forwards placeholder prop', () => {
    render(<Input placeholder="Enter text..." />);
    expect(screen.getByPlaceholderText('Enter text...')).toBeInTheDocument();
  });

  it('sets aria-invalid when error is present', () => {
    render(<Input error="Error" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  it('applies full width class', () => {
    const { container } = render(<Input fullWidth />);
    const formGroup = container.querySelector('.form-group');
    expect(formGroup).toHaveClass('form-group-full-width');
  });

  it('applies custom className', () => {
    render(<Input className="custom-input" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('custom-input');
  });
});

describe('TextArea Component', () => {
  it('renders textarea field', () => {
    render(<TextArea />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<TextArea label="Message" />);
    expect(screen.getByLabelText('Message')).toBeInTheDocument();
  });

  it('shows required asterisk when required', () => {
    render(<TextArea label="Comment" required />);
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('renders with help text', () => {
    render(<TextArea helpText="Maximum 500 characters" />);
    expect(screen.getByText('Maximum 500 characters')).toBeInTheDocument();
  });

  it('renders with error message', () => {
    render(<TextArea error="Message is required" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Message is required')).toBeInTheDocument();
  });

  it('applies error class when error is present', () => {
    render(<TextArea error="Error" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('form-input-error');
  });

  it('handles value changes', async () => {
    const user = userEvent.setup();
    render(<TextArea />);
    const textarea = screen.getByRole('textbox');

    await user.type(textarea, 'test message');
    expect(textarea).toHaveValue('test message');
  });

  it('forwards rows prop', () => {
    render(<TextArea rows={10} />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('rows', '10');
  });

  it('forwards placeholder prop', () => {
    render(<TextArea placeholder="Enter your message..." />);
    expect(screen.getByPlaceholderText('Enter your message...')).toBeInTheDocument();
  });
});
