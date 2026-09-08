// AIR Cloud client for the console. Unlike api/live.ts (the legacy console
// contract), every call here maps to a route that exists in
// src/vindicara/cloud/routes. Authentication is the AIR Cloud session token
// obtained from POST /v1/auth/exchange; a 401 triggers exactly one
// re-exchange with the stored Auth0 token before the error surfaces.
import type {
  ExchangeResponse,
  IssuedKey,
  RedactedKey,
  RunDetail,
  RunRecordsPage,
  RunsPage,
  CloudWorkspace
} from './cloud-types';

export class CloudError extends Error {
  constructor(
    message: string,
    public readonly status: number
  ) {
    super(message);
  }
}

export interface CloudSessionSource {
  token(): string | null;
  refresh(): Promise<string | null>;
}

export class CloudClient {
  constructor(
    private readonly base: string,
    private readonly session: CloudSessionSource,
    private readonly fetchImpl: typeof fetch = fetch
  ) {}

  async exchange(auth0Token: string): Promise<ExchangeResponse> {
    const res = await this.fetchImpl(`${this.base}/v1/auth/exchange`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ token: auth0Token })
    });
    if (!res.ok) throw new CloudError(await detail(res), res.status);
    return (await res.json()) as ExchangeResponse;
  }

  me(): Promise<CloudWorkspace> {
    return this.request<CloudWorkspace>('GET', '/v1/workspaces/me');
  }

  listKeys(): Promise<RedactedKey[]> {
    return this.request<RedactedKey[]>('GET', '/v1/keys');
  }

  issueKey(input: { name: string; role: string }): Promise<IssuedKey> {
    return this.request<IssuedKey>('POST', '/v1/keys', input);
  }

  revokeKey(keyId: string): Promise<void> {
    return this.request<void>('DELETE', `/v1/keys/${encodeURIComponent(keyId)}`);
  }

  listRuns(opts: { limit?: number; offset?: number } = {}): Promise<RunsPage> {
    const q = new URLSearchParams({ limit: String(opts.limit ?? 50), offset: String(opts.offset ?? 0) });
    return this.request<RunsPage>('GET', `/v1/runs?${q}`);
  }

  getRun(runId: string): Promise<RunDetail> {
    return this.request<RunDetail>('GET', `/v1/runs/${encodeURIComponent(runId)}`);
  }

  getRunRecords(runId: string, opts: { limit?: number; offset?: number } = {}): Promise<RunRecordsPage> {
    const q = new URLSearchParams({ limit: String(opts.limit ?? 100), offset: String(opts.offset ?? 0) });
    return this.request<RunRecordsPage>('GET', `/v1/runs/${encodeURIComponent(runId)}/records?${q}`);
  }

  private async request<T>(method: string, path: string, body?: unknown, retried = false): Promise<T> {
    const token = this.session.token();
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    const res = await this.fetchImpl(`${this.base}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body)
    });
    if (res.status === 401 && !retried) {
      const fresh = await this.session.refresh();
      if (fresh) return this.request<T>(method, path, body, true);
    }
    if (!res.ok) throw new CloudError(await detail(res), res.status);
    if (res.status === 204) return undefined as T;
    const text = await res.text();
    return (text ? JSON.parse(text) : undefined) as T;
  }
}

async function detail(res: Response): Promise<string> {
  try {
    const parsed = (await res.json()) as { detail?: unknown };
    if (typeof parsed.detail === 'string') return parsed.detail;
    return `${res.status} ${res.statusText}`;
  } catch {
    return `${res.status} ${res.statusText}`;
  }
}
