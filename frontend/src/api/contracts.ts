import client from './client';
import type { Contract, ContractListResponse } from '../types';

export async function listContracts(params?: {
  search?: string;
  status?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}): Promise<ContractListResponse> {
  const res = await client.get('/contracts', { params });
  return res.data;
}

export async function createContract(data: {
  title: string;
  contract_no: string;
  party_a: string;
  party_b: string;
  amount?: number;
  sign_date?: string;
  expiry_date?: string;
  content?: string;
}): Promise<Contract> {
  const res = await client.post('/contracts', data);
  return res.data;
}

export async function getContract(id: number): Promise<Contract> {
  const res = await client.get(`/contracts/${id}`);
  return res.data;
}

export async function updateContract(
  id: number,
  data: {
    title?: string;
    contract_no?: string;
    party_a?: string;
    party_b?: string;
    amount?: number;
    sign_date?: string | null;
    expiry_date?: string | null;
    content?: string;
  }
): Promise<Contract> {
  const res = await client.put(`/contracts/${id}`, data);
  return res.data;
}

export async function deleteContract(id: number): Promise<void> {
  await client.delete(`/contracts/${id}`);
}

export async function updateContractStatus(
  id: number,
  status: string
): Promise<Contract> {
  const res = await client.patch(`/contracts/${id}/status`, { status });
  return res.data;
}
