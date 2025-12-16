import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card } from '../../components/Card';

describe('Card Component', () => {
  it('renders with children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders with title', () => {
    render(<Card title="Card Title">Content</Card>);
    expect(screen.getByText('Card Title')).toBeInTheDocument();
  });

  it('renders with description', () => {
    render(<Card description="Card description">Content</Card>);
    expect(screen.getByText('Card description')).toBeInTheDocument();
  });

  it('renders light variant by default', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass('card');
    expect(card).not.toHaveClass('card-dark');
  });

  it('renders dark variant', () => {
    const { container } = render(<Card variant="dark">Content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass('card-dark');
  });

  it('applies hoverable class when hoverable is true', () => {
    const { container } = render(<Card hoverable>Content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass('card-hoverable');
  });

  it('applies clickable class when clickable is true', () => {
    const { container } = render(<Card clickable>Content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass('card-clickable');
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass('custom-class');
  });

  it('renders title and description together', () => {
    render(
      <Card title="Title" description="Description">
        Content
      </Card>
    );
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
  });
});
