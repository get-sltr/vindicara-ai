// Security headers carried by the app itself, not a CloudFront edge — so the
// same container is secure behind our ALB AND when a customer self-hosts it in
// their own / air-gapped network (where there is no CloudFront). Mirrors the
// previous CloudFront ResponseHeaders policy (site_stack.py).
//
// connect-src must list every host the console fetches at runtime (the API
// gateway + Auth0), or the CSP silently blocks it. AIR_API_ORIGIN is injected
// by the Fargate task; it falls back to the current production API.

import { recordVisit } from '$lib/server/visitors.js';

const API_ORIGIN = process.env.AIR_API_ORIGIN || 'https://cloud.vindicara.io';
const AUTH0_ORIGIN = 'https://dev-kilt2vkudvbu75ny.us.auth0.com';

// Google Analytics 4 via gtag.js (loaded in app.html). gtag.js is served from
// googletagmanager.com; GA4 then beacons measurement hits to google-analytics.com
// (regional subdomains like region1.google-analytics.com + analytics.google.com)
// over fetch (connect-src) with an img pixel fallback (img-src). All three
// directives must allow these hosts or the CSP silently drops analytics.
const GTM_ORIGIN = 'https://www.googletagmanager.com';
const GA_ORIGINS = 'https://www.google-analytics.com https://*.google-analytics.com https://*.analytics.google.com';

const CSP = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "frame-src 'none'",
  `img-src 'self' data: blob: ${GTM_ORIGIN} ${GA_ORIGINS}`,
  "font-src 'self' https://fonts.gstatic.com",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  `script-src 'self' 'unsafe-inline' ${GTM_ORIGIN}`,
  `connect-src 'self' ${API_ORIGIN} ${AUTH0_ORIGIN} ${GTM_ORIGIN} ${GA_ORIGINS}`,
  "form-action 'self'",
  'upgrade-insecure-requests'
].join('; ');

// Canonical host for the site. www.vindicara.io serves the same app (the ACM
// cert carries it as a SAN), so without this both hosts return 200 and Google
// treats them as duplicates. Collapse www -> apex with a 301 so there is exactly
// one indexable host. Built literally (not by mutating event.url) to avoid the
// ":443" artifact the ALB's http->https redirect leaves in its Location header.
const CANONICAL_HOST = 'vindicara.io';

/** @type {import('@sveltejs/kit').Handle} */
export async function handle({ event, resolve }) {
  // http -> https, at the app layer. The ALB forwards :80 here rather than doing
  // its own redirect, because the ALB redirect appends a literal ":443" to the
  // Location (https://vindicara.io:443/) which strict domain verifiers (e.g.
  // Google for Startups) read as "a different host". Building the Location from
  // CANONICAL_HOST here yields a clean https://vindicara.io/... with no port, and
  // collapses www -> apex in the same hop.
  if (event.request.headers.get('x-forwarded-proto') === 'http') {
    return new Response(null, {
      status: 301,
      headers: { location: `https://${CANONICAL_HOST}${event.url.pathname}${event.url.search}` }
    });
  }
  // Host header reflects the real request (no ORIGIN pinned in the Fargate task,
  // so adapter-node derives event.url from it). Redirect www -> apex first, then
  // the moved console URL, so a request to www/dashboard resolves in one hop each.
  const host = event.request.headers.get('host') || event.url.host;
  if (host === `www.${CANONICAL_HOST}`) {
    return new Response(null, {
      status: 301,
      headers: { location: `https://${CANONICAL_HOST}${event.url.pathname}${event.url.search}` }
    });
  }
  // The Flightdeck console moved from /dashboard to /flightdeck. Keep the old
  // human-facing URL working with a permanent redirect.
  if (event.url.pathname === '/dashboard' || event.url.pathname.startsWith('/dashboard/')) {
    const rest = event.url.pathname.slice('/dashboard'.length);
    return new Response(null, {
      status: 301,
      headers: { location: `https://${CANONICAL_HOST}/flightdeck${rest}${event.url.search}` }
    });
  }
  // Axiisium now has its own product site (axiisium.com). The old vindicara.io
  // /axiisium pages are stale; send the whole tree there with a permanent redirect
  // so there is one canonical, polished destination.
  // The /blog/introducing-axiisium post was removed with the rest of the
  // Axiisium content; it was indexed, so forward it rather than 404.
  if (event.url.pathname === '/blog/introducing-axiisium') {
    return new Response(null, {
      status: 301,
      headers: { location: 'https://axiisium.com' }
    });
  }
  if (event.url.pathname === '/axiisium' || event.url.pathname.startsWith('/axiisium/')) {
    return new Response(null, {
      status: 301,
      headers: { location: `https://axiisium.com${event.url.search}` }
    });
  }

  recordVisit(event); // keyless live-map: tag real visitors (fire-and-forget, never blocks)
  const response = await resolve(event);
  response.headers.set('Content-Security-Policy', CSP);
  response.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  return response;
}
