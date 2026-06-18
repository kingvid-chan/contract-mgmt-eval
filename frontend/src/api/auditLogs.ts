import client from './client';
import type { AuditLogFilter, AuditLogListResponse } from '../types';

export async function listAuditLogs(
  params: AuditLogFilter = {}
): Promise<AuditLogListResponse> {
  const response = await client.get<AuditLogListResponse>('/audit-logs', { params });
  return response.data;
}
