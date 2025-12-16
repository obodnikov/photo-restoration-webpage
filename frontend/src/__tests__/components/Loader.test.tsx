import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Loader } from '../../components/Loader';

describe('Loader Component', () => {
  it('renders loader with default size (medium)', () => {
    const { container } = render(<Loader />);
    const spinner = container.querySelector('.loader-spinner');
    expect(spinner).toHaveClass('loader-medium');
  });

  it('renders small loader', () => {
    const { container } = render(<Loader size="small" />);
    const spinner = container.querySelector('.loader-spinner');
    expect(spinner).toHaveClass('loader-small');
  });

  it('renders large loader', () => {
    const { container } = render(<Loader size="large" />);
    const spinner = container.querySelector('.loader-spinner');
    expect(spinner).toHaveClass('loader-large');
  });

  it('renders with text', () => {
    render(<Loader text="Loading..." />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('does not render text when not provided', () => {
    const { container } = render(<Loader />);
    const text = container.querySelector('.loader-text');
    expect(text).not.toBeInTheDocument();
  });

  it('renders in fullscreen mode', () => {
    const { container } = render(<Loader fullscreen />);
    const loaderContainer = container.querySelector('.loader-container');
    expect(loaderContainer).toHaveClass('loader-fullscreen');
  });

  it('does not render in fullscreen mode by default', () => {
    const { container } = render(<Loader />);
    const loaderContainer = container.querySelector('.loader-container');
    expect(loaderContainer).not.toHaveClass('loader-fullscreen');
  });

  it('applies custom className', () => {
    const { container } = render(<Loader className="custom-loader" />);
    const loaderContainer = container.querySelector('.loader-container');
    expect(loaderContainer).toHaveClass('custom-loader');
  });
});
