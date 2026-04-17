/**
 * auth.js
 * Helper de autenticacion JWT para SAAS COREM (SimpleJWT).
 *
 * SAAS COREM usa django-tenants: el header Host determina el schema
 * de la base de datos que Django utiliza. Sin el Host correcto, el
 * endpoint retorna 404 o usa el schema publico equivocado.
 *
 * Endpoint: POST /api/v1/auth/token/
 * Body:     { "email": "...", "password": "..." }
 * Response: { "access": "<JWT>", "refresh": "<JWT>" }
 */

import http  from 'k6/http';
import { check, fail } from 'k6';
import { Trend } from 'k6/metrics';

export const authDuration = new Trend('auth_duration', true);

/**
 * Obtiene un par de tokens JWT (access + refresh) para un usuario dado.
 *
 * Se llama tipicamente en la funcion setup() de k6 para que el token
 * sea obtenido una sola vez y compartido entre todos los VUs.
 *
 * @param {string} apiBase     - URL base de la API, ej: 'http://localhost:8000/api/v1'
 * @param {string} tenantHost  - Header Host del tenant, ej: 'garabato.localhost'
 * @param {string} email       - Email del usuario
 * @param {string} password    - Password del usuario
 * @returns {{ access: string, refresh: string }}
 */
export function getTokens(apiBase, tenantHost, email, password) {
  const url     = `${apiBase}/auth/token/`;
  const payload = JSON.stringify({ email, password });
  const headers = {
    'Content-Type': 'application/json',
    'Accept':       'application/json',
    'Host':         tenantHost,
  };

  const start    = Date.now();
  const response = http.post(url, payload, { headers, tags: { endpoint: 'auth_token' } });
  authDuration.add(Date.now() - start);

  const ok = check(response, {
    'auth/token: status 200':           (r) => r.status === 200,
    'auth/token: tiene access token':   (r) => !!r.json('access'),
    'auth/token: tiene refresh token':  (r) => !!r.json('refresh'),
  });

  if (!ok) {
    fail(
      `Fallo la autenticacion para ${email}. ` +
      `Status: ${response.status}. Body: ${response.body.substring(0, 200)}`
    );
  }

  return {
    access:  response.json('access'),
    refresh: response.json('refresh'),
  };
}

/**
 * Refresca el access token usando el refresh token.
 * Util en tests largos (soak) donde el access token puede expirar.
 *
 * @param {string} apiBase    - URL base de la API
 * @param {string} tenantHost - Header Host del tenant
 * @param {string} refreshToken
 * @returns {string} Nuevo access token
 */
export function refreshAccessToken(apiBase, tenantHost, refreshToken) {
  const url     = `${apiBase}/auth/token/refresh/`;
  const payload = JSON.stringify({ refresh: refreshToken });
  const headers = {
    'Content-Type': 'application/json',
    'Accept':       'application/json',
    'Host':         tenantHost,
  };

  const response = http.post(url, payload, { headers, tags: { endpoint: 'auth_refresh' } });

  check(response, {
    'auth/token/refresh: status 200':        (r) => r.status === 200,
    'auth/token/refresh: nuevo access token': (r) => !!r.json('access'),
  });

  if (response.status !== 200) {
    fail(`Fallo el refresh del token. Status: ${response.status}`);
  }

  return response.json('access');
}

/**
 * Construye el objeto de headers autenticados para todas las requests.
 * Incluye el header Host requerido por django-tenants.
 *
 * @param {string} accessToken
 * @param {string} tenantHost
 * @returns {object} Headers HTTP
 */
export function authHeaders(accessToken, tenantHost) {
  return {
    'Content-Type':  'application/json',
    'Accept':        'application/json',
    'Authorization': `Bearer ${accessToken}`,
    'Host':          tenantHost,
  };
}

/**
 * Construye headers autenticados para descargar archivos binarios (Excel, PDF).
 *
 * @param {string} accessToken
 * @param {string} tenantHost
 * @returns {object} Headers HTTP para descarga binaria
 */
export function authHeadersBinary(accessToken, tenantHost) {
  return {
    'Accept':        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream',
    'Authorization': `Bearer ${accessToken}`,
    'Host':          tenantHost,
  };
}

/**
 * Obtiene tokens para multiples roles simultaneamente.
 * Util en la funcion setup() de tests que simulan varios perfiles.
 *
 * @param {string} apiBase
 * @param {string} tenantHost
 * @param {object} credentials - { roleName: { email, password }, ... }
 * @returns {object} { roleName: { access, refresh }, ... }
 */
export function getMultiRoleTokens(apiBase, tenantHost, credentials) {
  const tokens = {};
  for (const [role, creds] of Object.entries(credentials)) {
    tokens[role] = getTokens(apiBase, tenantHost, creds.email, creds.password);
  }
  return tokens;
}
