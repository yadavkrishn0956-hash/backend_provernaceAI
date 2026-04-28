const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

export interface ProcessResponse {
  asset_id: string;
  input_mode: 'prompt' | 'upload';
  signature_alg: string;
  watermark_version: string;
  protected_image_ref: string;
  created_at: string;
  message: string;
}

export interface VerifySignalSummary {
  signature_valid: boolean;
  watermark_detected: boolean;
  local_mac_valid?: boolean | null;
  db_record_found?: boolean | null;
  commitment_valid?: boolean | null;
  current_pdq_hash_hex?: string | null;
  current_semantic_hash_hex?: string | null;
  pdq_distance?: number | null;
  clip_similarity?: number | null;
  pdq_result?: string | null;
  clip_result?: string | null;
}

export interface VerifyResponse {
  asset_id: string | null;
  verdict: string;
  signals: VerifySignalSummary;
  gemini_explanation: string | null;
  reasons: string[];
  verified_at: string;
}

export interface RecordResponse {
  asset_id: string;
  payload: Record<string, unknown>;
  signature_b64: string;
  pdq_hash_hex: string;
  semantic_hash_hex: string;
  commitment: string | null;
  mini_mac: string | null;
  clip_embedding: number[] | null;
  created_at: string;
  updated_at: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  checks: Record<string, boolean>;
}

export async function processImage(formData: FormData): Promise<ProcessResponse> {
  const res = await fetch(`${API_BASE}/process`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || err.detail || 'Process failed');
  }
  return res.json();
}

export async function verifyImage(formData: FormData): Promise<VerifyResponse> {
  const res = await fetch(`${API_BASE}/verify`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || err.detail || 'Verification failed');
  }
  return res.json();
}

export async function getRecord(assetId: string): Promise<RecordResponse> {
  const res = await fetch(`${API_BASE}/records/${assetId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || err.detail || 'Record not found');
  }
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export function getAssetImageUrl(assetId: string): string {
  return `${API_BASE}/assets/${assetId}/image`;
}
