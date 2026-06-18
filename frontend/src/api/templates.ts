import client from './client';
import type { ContractTemplate, TemplateListResponse, TemplateDropdownItem } from '../types';

export async function listTemplates(params?: {
  search?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}): Promise<TemplateListResponse> {
  const res = await client.get('/templates', { params });
  return res.data;
}

export async function listTemplatesDropdown(): Promise<TemplateDropdownItem[]> {
  const res = await client.get('/templates/dropdown');
  return res.data;
}

export async function createTemplate(data: {
  name: string;
  category?: string;
  party_a_default?: string;
  party_b_default?: string;
  content?: string;
  amount_min?: number;
  amount_max?: number;
}): Promise<ContractTemplate> {
  const res = await client.post('/templates', data);
  return res.data;
}

export async function getTemplate(id: number): Promise<ContractTemplate> {
  const res = await client.get(`/templates/${id}`);
  return res.data;
}

export async function updateTemplate(
  id: number,
  data: {
    name?: string;
    category?: string;
    party_a_default?: string | null;
    party_b_default?: string | null;
    content?: string;
    amount_min?: number | null;
    amount_max?: number | null;
  }
): Promise<ContractTemplate> {
  const res = await client.put(`/templates/${id}`, data);
  return res.data;
}

export async function deleteTemplate(id: number): Promise<void> {
  await client.delete(`/templates/${id}`);
}
