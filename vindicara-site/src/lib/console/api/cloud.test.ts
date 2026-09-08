import { describe, expect, it } from 'vitest';
import { CloudClient, CloudError } from './cloud';

interface Call {
  url: string;
  method: string;
  headers: Record<string, string>;
  body: string | undefined;
}

function fakeFetch(responses: Array<{ status: number; body: unknown }>, calls: Call[]): typeof fetch {
  return (async (input: RequestInfo | URL, init?: RequestInit) => {
    calls.push({
      url: String(input),
      method: init?.method ?? 'GET',
      headers: (init?.headers as Record<string, string>) ?? {},
      body: typeof init?.body === 'string' ? init.body : undefined
    });
    const next = responses.shift() ?? { status: 500, body: { detail: 'no response scripted' } };
    return new Response(JSON.stringify(next.body), { status: next.status, statusText: 'x', headers: { 'Content-Type': 'application/json' } });
  }) as typeof fetch;
}

describe('CloudClient', () => {
  it('posts the identity token to the exchange route', async () => {
    const calls: Call[] = [];
    const client = new CloudClient('http://cloud.test', { token: () => null, refresh: async () => null }, fakeFetch([{ status: 201, body: { api_key: 'air_x', workspace: { workspace_id: 'ws' } } }], calls));
    const r = await client.exchange('auth0-token');
    expect(calls[0].url).toBe('http://cloud.test/v1/auth/exchange');
    expect(calls[0].method).toBe('POST');
    expect(JSON.parse(calls[0].body ?? '{}')).toEqual({ token: 'auth0-token' });
    expect(r.api_key).toBe('air_x');
  });

  it('sends the session token as Bearer and re-exchanges exactly once on 401', async () => {
    const calls: Call[] = [];
    let token = 'stale';
    const client = new CloudClient(
      'http://cloud.test',
      { token: () => token, refresh: async () => { token = 'fresh'; return token; } },
      fakeFetch([{ status: 401, body: { detail: 'expired' } }, { status: 200, body: { workspace_id: 'ws', count: 0, runs: [] } }], calls)
    );
    const page = await client.listRuns({ limit: 5 });
    expect(page.count).toBe(0);
    expect(calls.map((c) => c.headers.Authorization)).toEqual(['Bearer stale', 'Bearer fresh']);
    expect(calls[0].url).toBe('http://cloud.test/v1/runs?limit=5&offset=0');
  });

  it('surfaces the server detail when the retry also fails', async () => {
    const calls: Call[] = [];
    const client = new CloudClient('http://cloud.test', { token: () => 't', refresh: async () => 't' }, fakeFetch([{ status: 401, body: { detail: 'a' } }, { status: 401, body: { detail: 'still expired' } }], calls));
    await expect(client.listKeys()).rejects.toMatchObject({ status: 401, message: 'still expired' } satisfies Partial<CloudError>);
    expect(calls).toHaveLength(2);
  });

  it('revoke and issue hit the keys routes', async () => {
    const calls: Call[] = [];
    const client = new CloudClient('http://cloud.test', { token: () => 't', refresh: async () => null }, fakeFetch([{ status: 201, body: { key_id: 'k', key: 'air_new' } }, { status: 200, body: { revoked: true } }], calls));
    const issued = await client.issueKey({ name: 'laptop', role: 'member' });
    expect(issued.key).toBe('air_new');
    await client.revokeKey('key_ws_0001');
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual(['POST http://cloud.test/v1/keys', 'DELETE http://cloud.test/v1/keys/key_ws_0001']);
  });
});
