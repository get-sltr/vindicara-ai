// The AIR Cloud session: what POST /v1/auth/exchange handed back, minus the
// API key. The key is held in memory only (freshApiKey) and shown once on the
// Keys screen; it never reaches sessionStorage. The Auth0 token that produced
// the session stays in stores/session so a 401 can be repaired by
// re-exchanging without sending the person back through Auth0.
import { get, writable } from 'svelte/store';
import { env } from '$env/dynamic/public';
import { CloudClient } from '$lib/console/api/cloud';
import type { CloudWorkspace, ExchangeResponse } from '$lib/console/api/cloud-types';
import { sessionToken } from '$lib/console/stores/session';

export interface CloudSession {
  session_token: string;
  workspace: CloudWorkspace;
  role: string;
  key_id: string;
  cloud_url: string;
  console_url: string;
  email: string | null;
  obtained_at: number;
}

const STORAGE_KEY = 'air_flightdeck_cloud';

function load(): CloudSession | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as CloudSession) : null;
  } catch {
    return null;
  }
}

export const cloudSession = writable<CloudSession | null>(typeof sessionStorage === 'undefined' ? null : load());
export const freshApiKey = writable<string | null>(null);
export const cloudError = writable<string | null>(null);

function persist(session: CloudSession | null): void {
  cloudSession.set(session);
  try {
    if (session) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    else sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* storage unavailable */
  }
}

export function cloudBase(): string {
  return (get(cloudSession)?.cloud_url ?? env.PUBLIC_AIR_API_BASE ?? '').replace(/\/$/, '');
}

export const cloud = new CloudClient(env.PUBLIC_AIR_API_BASE ?? '', {
  token: () => get(cloudSession)?.session_token ?? null,
  refresh: async () => {
    const auth0 = get(sessionToken);
    if (!auth0) return null;
    try {
      const r = await establishCloudSession(auth0);
      return r.session_token;
    } catch {
      return null;
    }
  }
});

function toSession(r: ExchangeResponse): CloudSession {
  return {
    session_token: r.session_token,
    workspace: r.workspace,
    role: r.role,
    key_id: r.key_id,
    cloud_url: r.cloud_url,
    console_url: r.console_url,
    email: r.email,
    obtained_at: Date.now()
  };
}

// Trade the Auth0 token for the AIR Cloud session. Called from the auth
// callback and on a 401. The key, when present, is exposed once via
// freshApiKey and never written to storage.
export async function establishCloudSession(auth0Token: string): Promise<ExchangeResponse> {
  cloudError.set(null);
  const r = await cloud.exchange(auth0Token);
  persist(toSession(r));
  if (r.api_key) freshApiKey.set(r.api_key);
  return r;
}

export function clearCloudSession(): void {
  persist(null);
  freshApiKey.set(null);
}

export function forgetFreshKey(): void {
  freshApiKey.set(null);
}
