import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./FlightdeckSignIn.svelte', import.meta.url)), 'utf8');

describe('FlightdeckSignIn', () => {
	it('uses the configured Auth0 social connections', () => {
		expect(source).toContain("beginAuth0Login('google-oauth2')");
		expect(source).toContain("beginAuth0Login('github')");
		expect(source).toContain('beginAuth0Login()');
	});

	it('keeps two cards and no terminal in the trust rail', () => {
		expect(source).toContain('Signed local evidence');
		expect(source).toContain('Findings you can inspect');
		expect(source).not.toContain('terminal-body');
	});
});
