import client from './client';
import type { User, UserListResponse } from '../types';

export async function listUsers(params?: {
  search?: string;
  role?: string;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<UserListResponse> {
  const res = await client.get('/users', { params });
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await client.get('/users/me');
  return res.data;
}

export async function createUser(data: {
  username: string;
  email: string;
  password: string;
  role: string;
}): Promise<User> {
  const res = await client.post('/users', data);
  return res.data;
}

export async function getUser(id: number): Promise<User> {
  const res = await client.get(`/users/${id}`);
  return res.data;
}

export async function updateUser(
  id: number,
  data: { username?: string; email?: string; password?: string; role?: string }
): Promise<User> {
  const res = await client.put(`/users/${id}`, data);
  return res.data;
}

export async function toggleUserStatus(id: number, status: string): Promise<User> {
  const res = await client.patch(`/users/${id}/status`, { status });
  return res.data;
}
