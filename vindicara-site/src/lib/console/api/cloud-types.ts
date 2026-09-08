// Shapes returned by AIR Cloud (src/vindicara/cloud). Kept in one place so the
// Keys and Runs screens and the CLI agree on field names.
import type { AgDRRecord, Finding, VerificationResult } from '$lib/console/forensics/types';

export interface CloudWorkspace {
  workspace_id: string;
  name: string;
  owner_email: string;
  created_at: string;
  tier: 'free' | 'pro' | 'team' | 'enterprise' | string;
}

export interface ExchangeResponse {
  session_token: string;
  workspace: CloudWorkspace;
  role: string;
  key_id: string;
  api_key: string | null; // shown once: only on the sign-in that minted it
  created: boolean;
  email: string | null;
  sub: string;
  cloud_url: string;
  console_url: string;
}

export interface RedactedKey {
  key_id: string;
  workspace_id: string;
  role: string;
  name: string | null;
  created_at: string;
  revoked_at: string | null;
}

export interface IssuedKey extends RedactedKey {
  key: string; // the secret, returned exactly once
}

export interface RunSummary {
  run_id: string;
  workspace_id: string;
  api_key_id: string;
  first_at: string;
  last_at: string;
  records: number;
  kinds: Record<string, number>;
  user_intent: string | null;
  signer_key: string;
  verification: 'ok' | 'tampered' | 'broken_chain' | null;
  findings: number | null;
  max_severity: string | null;
  assessed_at: string | null;
  console_url: string;
}

export interface RunsPage {
  workspace_id: string;
  count: number;
  runs: RunSummary[];
}

export interface Authority {
  kind: string;
  subject: string | null;
  issuer: string | null;
  detail: string;
}

export interface TimelineEntry {
  ordinal: number;
  step_id: string;
  timestamp: string;
  kind: string;
  summary: string;
  authority: Authority;
  evidence: 'anchored' | 'signed' | 'gap' | 'unverified';
  evidence_detail: string;
  findings: string[];
  target: boolean;
  in_ancestry: boolean;
}

export interface IncidentTimeline {
  focus: string | null;
  anchors: number;
  entries: TimelineEntry[];
  gaps: string[];
}

export interface HealthCheck {
  key: string;
  title: string;
  level: 'ok' | 'warn' | 'fail';
  detail: string;
}

export interface EvidenceHealth {
  level: 'ok' | 'warn' | 'fail';
  checks: HealthCheck[];
}

export interface RunDetail {
  summary: RunSummary;
  verification: VerificationResult;
  findings: Finding[];
  timeline: IncidentTimeline;
  health: EvidenceHealth;
  console_url: string;
}

export interface RunRecordsPage {
  run_id: string;
  count: number;
  offset: number;
  records: AgDRRecord[];
}
