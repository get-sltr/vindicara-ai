// The signed-in operator — the human the session (and any approvals) are bound to.
// Their name + organization show in the top-bar identity chip, and they are the
// authorizer captured in HUMAN_APPROVAL records and highlighted in court reports.
import { derived, writable } from 'svelte/store';
import { persisted } from './persisted';

// Controls the sign-in modal so any surface (top bar, operator card) can open it.

export interface Operator {
  name: string;
  organization: string;
  role: string;
  email: string;
  authMethod: 'passkey' | 'auth0';
  signedInAt: string | null; // ISO timestamp
}

const SIGNED_OUT: Operator = {
  name: '',
  organization: '',
  role: '',
  email: '',
  authMethod: 'passkey',
  signedInAt: null
};

export const operator = persisted<Operator>('air.console.operator', SIGNED_OUT);
export const signedIn = derived(operator, ($o) => $o.signedInAt !== null);

export interface SignInInput {
  name: string;
  organization: string;
  role?: string;
  email?: string;
  authMethod?: 'passkey' | 'auth0';
}

export function signIn(input: SignInInput): void {
  const name = input.name.trim() || 'Operator';
  const organization = input.organization.trim() || 'Unspecified organization';
  const slug = name.toLowerCase().replace(/[^a-z]+/g, '.').replace(/^\.|\.$/g, '');
  operator.set({
    name,
    organization,
    role: input.role?.trim() || 'Clinician',
    email: input.email?.trim() || `${slug || 'operator'}@${orgDomain(organization)}`,
    authMethod: input.authMethod ?? 'passkey',
    signedInAt: new Date().toISOString()
  });
}

export function signOut(): void {
  operator.set({ ...SIGNED_OUT });
}

// Auth0-style subject claim for the chain (who authorized an action).
export function operatorSub(op: Operator): string {
  const slug = op.name.toLowerCase().replace(/[^a-z]+/g, '.').replace(/^\.|\.$/g, '');
  return `auth0|${slug || 'operator'}`;
}

function orgDomain(org: string): string {
  const base = org.toLowerCase().replace(/[^a-z0-9]+/g, '');
  return `${base || 'org'}.example`;
}
