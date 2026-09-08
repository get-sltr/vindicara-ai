import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { DEFAULT_CLOUD_URL, KEY_PLACEHOLDER, SNIPPETS, runLinkHint, shellHeader } from './snippets';

describe('setup snippets', () => {
  it('match the real SDK signatures', () => {
    for (const s of SNIPPETS) {
      expect(s.code).toContain('AIRRecorder(user_intent=');
      expect(s.code).not.toContain('AIRRecorder("chain.jsonl"');
    }
    const langchain = SNIPPETS.find((s) => s.id === 'langchain');
    expect(langchain?.code).toContain('AIRCallbackHandler(recorder=recorder)');
    expect(langchain?.code).not.toContain('AIRCallbackHandler(recorder)');
    for (const id of ['openai', 'anthropic', 'gemini', 'llamaindex']) {
      expect(SNIPPETS.find((s) => s.id === id)?.code).toMatch(/instrument_\w+\(.+, recorder\)/);
    }
  });

  it('shell header pins the release and only adds the URL when it is not the hosted default', () => {
    expect(shellHeader(null, DEFAULT_CLOUD_URL)).toBe(`pip install "projectair>=1.4"\nexport AIRSDK_CLOUD_API_KEY=${KEY_PLACEHOLDER}`);
    expect(shellHeader('air_abc', 'http://127.0.0.1:9477/')).toContain('export AIRSDK_CLOUD_API_KEY=air_abc');
    expect(shellHeader('air_abc', 'http://127.0.0.1:9477/')).toContain('export AIRSDK_CLOUD_URL=http://127.0.0.1:9477');
    expect(runLinkHint('https://vindicara.io/flightdeck/')).toBe('Run it. The terminal prints your run link: https://vindicara.io/flightdeck/runs/<run_id>');
  });

  it('the fresh key never reaches storage, and the fake sign-in surfaces are gone', () => {
    const store = readFileSync(fileURLToPath(new URL('../../stores/cloud.ts', import.meta.url)), 'utf8');
    expect(store).toContain('export const freshApiKey = writable<string | null>(null)');
    expect(store).not.toMatch(/sessionStorage\.setItem\([^)]*api_key/);
    const layout = readFileSync(fileURLToPath(new URL('../../../../routes/flightdeck/+layout.svelte', import.meta.url)), 'utf8');
    expect(layout).not.toContain('LockScreen');
    expect(layout).not.toContain('forensics/SignIn');
    const getStarted = readFileSync(fileURLToPath(new URL('../../../../routes/get-started/+page.svelte', import.meta.url)), 'utf8');
    expect(getStarted).toContain("import { SNIPPETS, shellHeader } from '$lib/console/screens/keys/snippets'");
    expect(getStarted).not.toContain('AIRCallbackHandler(recorder)]');
  });
});
