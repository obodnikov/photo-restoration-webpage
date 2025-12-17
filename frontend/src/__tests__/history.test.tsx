/**
 * Tests for history feature
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { HistoryCard } from '../features/history/components/HistoryCard';
import { HistoryList } from '../features/history/components/HistoryList';
import type { HistoryItem } from '../features/history/types';

const mockHistoryItem: HistoryItem = {
  id: '123',
  original_filename: 'test-photo.jpg',
  model_id: 'swin2sr-2x',
  created_at: '2024-12-15T10:00:00Z',
  original_path: '/uploads/original.jpg',
  processed_path: '/processed/processed.jpg',
};

const mockHistoryItems: HistoryItem[] = [
  mockHistoryItem,
  {
    id: '456',
    original_filename: 'another-photo.jpg',
    model_id: 'swin2sr-4x',
    created_at: '2024-12-14T10:00:00Z',
    original_path: '/uploads/original2.jpg',
    processed_path: '/processed/processed2.jpg',
  },
];

describe('HistoryCard Component', () => {
  it('renders history item details', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();

    render(
      <HistoryCard
        item={mockHistoryItem}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    expect(screen.getByText('test-photo.jpg')).toBeInTheDocument();
    expect(screen.getByText(/swin2sr-2x/i)).toBeInTheDocument();
  });

  it('displays thumbnail image', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();

    const { container } = render(
      <HistoryCard
        item={mockHistoryItem}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    const img = container.querySelector('img');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('alt', 'test-photo.jpg');
  });

  it('calls onView when view button clicked', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();

    render(
      <HistoryCard
        item={mockHistoryItem}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    fireEvent.click(screen.getByText('View'));
    expect(onView).toHaveBeenCalledWith(mockHistoryItem);
  });

  it('calls onDownload when download button clicked', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();

    render(
      <HistoryCard
        item={mockHistoryItem}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    fireEvent.click(screen.getByText('Download'));
    expect(onDownload).toHaveBeenCalledWith(mockHistoryItem);
  });

  it('calls onDelete when delete button clicked', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();

    render(
      <HistoryCard
        item={mockHistoryItem}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    fireEvent.click(screen.getByText('Delete'));
    expect(onDelete).toHaveBeenCalledWith(mockHistoryItem);
  });

  it('calls onView when image is clicked', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();

    const { container } = render(
      <HistoryCard
        item={mockHistoryItem}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    const imageContainer = container.querySelector('.history-card-image');
    fireEvent.click(imageContainer!);
    expect(onView).toHaveBeenCalledWith(mockHistoryItem);
  });
});

describe('HistoryList Component', () => {
  it('renders list of history items', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();
    const onPageChange = vi.fn();

    render(
      <HistoryList
        items={mockHistoryItems}
        loading={false}
        total={2}
        currentPage={1}
        pageSize={20}
        onPageChange={onPageChange}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    expect(screen.getByText('test-photo.jpg')).toBeInTheDocument();
    expect(screen.getByText('another-photo.jpg')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();
    const onPageChange = vi.fn();

    render(
      <HistoryList
        items={[]}
        loading={true}
        total={0}
        currentPage={1}
        pageSize={20}
        onPageChange={onPageChange}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    expect(screen.getByText('Loading history...')).toBeInTheDocument();
  });

  it('shows empty state when no items', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();
    const onPageChange = vi.fn();

    render(
      <HistoryList
        items={[]}
        loading={false}
        total={0}
        currentPage={1}
        pageSize={20}
        onPageChange={onPageChange}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    expect(screen.getByText('No History Yet')).toBeInTheDocument();
  });

  it('renders pagination controls when multiple pages', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();
    const onPageChange = vi.fn();

    render(
      <HistoryList
        items={mockHistoryItems}
        loading={false}
        total={50}
        currentPage={2}
        pageSize={20}
        onPageChange={onPageChange}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    expect(screen.getByText(/Page 2 of 3/i)).toBeInTheDocument();
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('disables previous button on first page', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();
    const onPageChange = vi.fn();

    render(
      <HistoryList
        items={mockHistoryItems}
        loading={false}
        total={50}
        currentPage={1}
        pageSize={20}
        onPageChange={onPageChange}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    const prevButton = screen.getByText('Previous');
    expect(prevButton).toBeDisabled();
  });

  it('disables next button on last page', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();
    const onPageChange = vi.fn();

    render(
      <HistoryList
        items={mockHistoryItems}
        loading={false}
        total={40}
        currentPage={2}
        pageSize={20}
        onPageChange={onPageChange}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    const nextButton = screen.getByText('Next');
    expect(nextButton).toBeDisabled();
  });

  it('calls onPageChange when pagination button clicked', () => {
    const onView = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();
    const onPageChange = vi.fn();

    render(
      <HistoryList
        items={mockHistoryItems}
        loading={false}
        total={50}
        currentPage={1}
        pageSize={20}
        onPageChange={onPageChange}
        onView={onView}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    fireEvent.click(screen.getByText('Next'));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
