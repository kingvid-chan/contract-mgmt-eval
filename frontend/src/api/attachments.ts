import client from './client';
import type { Attachment, AttachmentListResponse } from '../types';

export async function listAttachments(contractId: number): Promise<AttachmentListResponse> {
  const res = await client.get(`/contracts/${contractId}/attachments`);
  return res.data;
}

export async function uploadAttachment(contractId: number, file: File): Promise<Attachment> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await client.post(`/contracts/${contractId}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export function getDownloadUrl(attachmentId: number, preview = false): string {
  const token = localStorage.getItem('access_token') || '';
  let url = `/api/attachments/${attachmentId}/download?token=${encodeURIComponent(token)}`;
  if (preview) url += '&preview=true';
  return url;
}

export async function deleteAttachment(id: number): Promise<void> {
  await client.delete(`/attachments/${id}`);
}
