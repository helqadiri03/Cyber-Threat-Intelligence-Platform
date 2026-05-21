import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10_000,
});

// ── Types ──────────────────────────────────────────────────────────────────

export interface AttackTypeCount {
  attack_type: string;
  count: number;
}

export interface TopIpEntry {
  source_ip: string;
  count: number;
}

export interface TimelineBucket {
  timestamp: string;
  count: number;
}

export interface StatisticsResponse {
  source: string;
  total_predictions: number;
  total_alerts: number;
  top_attack: string | null;
  attack_breakdown: AttackTypeCount[];
  top_ips: TopIpEntry[];
  timeline: TimelineBucket[];
  updated_at: string;
}

export interface Prediction {
  id: string | null;
  source_ip: string;
  predicted_attack: string;
  confidence: number | null;
  risk_score?: number | null;
  model_version: string | null;
  features?: Record<string, unknown> | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// ── API calls ──────────────────────────────────────────────────────────────

export async function fetchStatistics(): Promise<StatisticsResponse> {
  const { data } = await api.get<StatisticsResponse>('/statistics');
  return data;
}

export async function fetchPredictions(params: {
  source_ip?: string;
  attack_type?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Prediction>> {
  const { data } = await api.get<PaginatedResponse<Prediction>>('/predictions', { params });
  return data;
}

export async function fetchHealth() {
  const { data } = await api.get('/health');
  return data;
}
