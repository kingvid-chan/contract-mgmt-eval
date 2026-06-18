import client from './client';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '../types';

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await client.post('/auth/login', data);
  return res.data;
}

export async function register(data: RegisterRequest): Promise<User> {
  const res = await client.post('/auth/register', data);
  return res.data;
}

export async function logout(): Promise<void> {
  await client.post('/auth/logout');
}

export async function getMe(): Promise<User> {
  const res = await client.get('/auth/me');
  return res.data;
}

export async function passwordReset(email: string): Promise<{ message: string; new_password?: string }> {
  const res = await client.post('/auth/password-reset', { email });
  return res.data;
}
