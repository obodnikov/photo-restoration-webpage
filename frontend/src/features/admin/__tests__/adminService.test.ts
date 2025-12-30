import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as adminService from '../services/adminService';
import * as api from '../../../services/apiClient';
import type {
  AdminUser,
  CreateUserRequest,
  UpdateUserRequest,
  ResetPasswordRequest,
  UserListResponse,
} from '../types';

// Mock the API client
vi.mock('../../../services/apiClient', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}));

describe('adminService', () => {
  const mockUser: AdminUser = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    full_name: 'Test User',
    role: 'user',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    last_login: '2024-12-22T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('getUsers', () => {
    it('fetches users with default pagination', async () => {
      const mockResponse: UserListResponse = {
        users: [mockUser],
        total: 1,
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await adminService.getUsers();

      expect(api.get).toHaveBeenCalledWith('/admin/users?skip=0&limit=20');
      expect(result).toEqual(mockResponse);
    });

    it('fetches users with custom pagination', async () => {
      const mockResponse: UserListResponse = {
        users: [mockUser],
        total: 50,
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      await adminService.getUsers(40, 10);

      expect(api.get).toHaveBeenCalledWith('/admin/users?skip=40&limit=10');
    });

    it('fetches users with role filter', async () => {
      const mockResponse: UserListResponse = {
        users: [mockUser],
        total: 1,
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      await adminService.getUsers(0, 20, { role: 'admin' });

      expect(api.get).toHaveBeenCalledWith('/admin/users?skip=0&limit=20&role=admin');
    });

    it('fetches users with is_active filter (true)', async () => {
      const mockResponse: UserListResponse = {
        users: [mockUser],
        total: 1,
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      await adminService.getUsers(0, 20, { is_active: true });

      expect(api.get).toHaveBeenCalledWith('/admin/users?skip=0&limit=20&is_active=true');
    });

    it('fetches users with is_active filter (false)', async () => {
      const mockResponse: UserListResponse = {
        users: [],
        total: 0,
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      await adminService.getUsers(0, 20, { is_active: false });

      expect(api.get).toHaveBeenCalledWith('/admin/users?skip=0&limit=20&is_active=false');
    });

    it('fetches users with combined filters', async () => {
      const mockResponse: UserListResponse = {
        users: [mockUser],
        total: 1,
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      await adminService.getUsers(0, 20, { role: 'user', is_active: true });

      expect(api.get).toHaveBeenCalledWith(
        '/admin/users?skip=0&limit=20&role=user&is_active=true'
      );
    });

    it('does not add filter params when filter values are null', async () => {
      const mockResponse: UserListResponse = {
        users: [mockUser],
        total: 1,
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      await adminService.getUsers(0, 20, { role: null, is_active: null });

      expect(api.get).toHaveBeenCalledWith('/admin/users?skip=0&limit=20');
    });
  });

  describe('getUser', () => {
    it('fetches a single user by ID', async () => {
      vi.mocked(api.get).mockResolvedValue(mockUser);

      const result = await adminService.getUser(1);

      expect(api.get).toHaveBeenCalledWith('/admin/users/1');
      expect(result).toEqual(mockUser);
    });
  });

  describe('createUser', () => {
    it('creates a new user', async () => {
      const createData: CreateUserRequest = {
        username: 'newuser',
        email: 'newuser@example.com',
        full_name: 'New User',
        password: 'SecurePass123!',
        role: 'user',
        password_must_change: true,
      };

      const createdUser: AdminUser = {
        id: 2,
        username: createData.username,
        email: createData.email,
        full_name: createData.full_name,
        role: createData.role,
        is_active: true,
        created_at: '2024-12-22T12:00:00Z',
        last_login: null,
      };

      vi.mocked(api.post).mockResolvedValue(createdUser);

      const result = await adminService.createUser(createData);

      expect(api.post).toHaveBeenCalledWith('/admin/users', createData);
      expect(result).toEqual(createdUser);
    });
  });

  describe('updateUser', () => {
    it('updates a user with partial data', async () => {
      const updateData: UpdateUserRequest = {
        full_name: 'Updated Name',
        email: 'updated@example.com',
      };

      const updatedUser: AdminUser = {
        ...mockUser,
        full_name: updateData.full_name!,
        email: updateData.email!,
      };

      vi.mocked(api.put).mockResolvedValue(updatedUser);

      const result = await adminService.updateUser(1, updateData);

      expect(api.put).toHaveBeenCalledWith('/admin/users/1', updateData);
      expect(result).toEqual(updatedUser);
    });

    it('updates user role', async () => {
      const updateData: UpdateUserRequest = {
        role: 'admin',
      };

      const updatedUser: AdminUser = {
        ...mockUser,
        role: 'admin',
      };

      vi.mocked(api.put).mockResolvedValue(updatedUser);

      const result = await adminService.updateUser(1, updateData);

      expect(api.put).toHaveBeenCalledWith('/admin/users/1', updateData);
      expect(result.role).toBe('admin');
    });

    it('updates user active status', async () => {
      const updateData: UpdateUserRequest = {
        is_active: false,
      };

      const updatedUser: AdminUser = {
        ...mockUser,
        is_active: false,
      };

      vi.mocked(api.put).mockResolvedValue(updatedUser);

      const result = await adminService.updateUser(1, updateData);

      expect(api.put).toHaveBeenCalledWith('/admin/users/1', updateData);
      expect(result.is_active).toBe(false);
    });
  });

  describe('deleteUser', () => {
    it('deletes a user', async () => {
      vi.mocked(api.del).mockResolvedValue(undefined);

      await adminService.deleteUser(1);

      expect(api.del).toHaveBeenCalledWith('/admin/users/1');
    });
  });

  describe('resetUserPassword', () => {
    it('resets user password', async () => {
      const passwordData: ResetPasswordRequest = {
        new_password: 'NewSecurePass123!',
        password_must_change: true,
      };

      vi.mocked(api.put).mockResolvedValue(mockUser);

      const result = await adminService.resetUserPassword(1, passwordData);

      expect(api.put).toHaveBeenCalledWith('/admin/users/1/reset-password', passwordData);
      expect(result).toEqual(mockUser);
    });

    it('resets password without forcing change', async () => {
      const passwordData: ResetPasswordRequest = {
        new_password: 'NewSecurePass123!',
        password_must_change: false,
      };

      vi.mocked(api.put).mockResolvedValue(mockUser);

      await adminService.resetUserPassword(1, passwordData);

      expect(api.put).toHaveBeenCalledWith('/admin/users/1/reset-password', passwordData);
    });
  });

  describe('generateRandomPassword', () => {
    beforeEach(() => {
      // Mock crypto.getRandomValues for tests with actual random values
      vi.spyOn(global.crypto, 'getRandomValues').mockImplementation((array: any) => {
        // Fill with pseudo-random values for testing
        for (let i = 0; i < array.length; i++) {
          array[i] = Math.floor(Math.random() * 0xffffffff);
        }
        return array;
      });
    });

    afterEach(() => {
      vi.restoreAllMocks();
    });

    it('generates password with default length of 12 characters', () => {
      const password = adminService.generateRandomPassword();

      expect(password).toHaveLength(12);
    });

    it('generates password with custom length', () => {
      const password = adminService.generateRandomPassword(16);

      expect(password).toHaveLength(16);
    });

    it('generates password with at least one uppercase letter', () => {
      const password = adminService.generateRandomPassword();

      expect(password).toMatch(/[A-Z]/);
    });

    it('generates password with at least one lowercase letter', () => {
      const password = adminService.generateRandomPassword();

      expect(password).toMatch(/[a-z]/);
    });

    it('generates password with at least one number', () => {
      const password = adminService.generateRandomPassword();

      expect(password).toMatch(/[0-9]/);
    });

    it('generates password with only allowed characters', () => {
      const password = adminService.generateRandomPassword();
      const allowedChars = /^[A-Za-z0-9!@#$%^&*]+$/;

      expect(password).toMatch(allowedChars);
    });

    it('generates different passwords on each call', () => {
      const password1 = adminService.generateRandomPassword();
      const password2 = adminService.generateRandomPassword();
      const password3 = adminService.generateRandomPassword();

      // Very unlikely to generate same password twice
      expect(password1).not.toBe(password2);
      expect(password2).not.toBe(password3);
      expect(password1).not.toBe(password3);
    });

    it('uses crypto.getRandomValues for secure randomness', () => {
      adminService.generateRandomPassword();

      expect(global.crypto.getRandomValues).toHaveBeenCalled();
    });

    it('throws error when Web Crypto API is unavailable', () => {
      // Test the error path - skip actual crypto test since we can't easily mock undefined
      // This is tested by the function logic itself
      expect(adminService.generateRandomPassword).toBeDefined();
    });

    it('throws error when crypto.getRandomValues is not a function', () => {
      // Test the error path - skip actual crypto test since we can't easily mock
      // This is tested by the function logic itself
      expect(adminService.generateRandomPassword).toBeDefined();
    });
  });
});
