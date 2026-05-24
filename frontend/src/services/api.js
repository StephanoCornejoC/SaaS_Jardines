import axios from "axios";

// In dev, requests go through Vite proxy (/api -> localhost:8000)
// In prod (Vercel), VITE_API_URL must be set to the Railway backend URL
const API_BASE = import.meta.env.VITE_API_URL || "";

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

/**
 * Extrae el slug del tenant desde el subdomain actual.
 *
 * Ejemplo: window.location.host = "garabato.miniddo.com"
 *   - parts = ["garabato", "miniddo", "com"]
 *   - Si hay >= 3 partes y la 2da es "miniddo", el tenant es la 1ra parte.
 *   - Si no, no hay tenant (apex miniddo.com o localhost en dev).
 *
 * El backend usa este header en TenantHeaderMiddleware para activar el
 * schema correcto cuando recibe requests cross-origin (Vercel → Railway).
 */
function detectTenantSlug() {
  if (typeof window === "undefined") return null;
  const host = window.location.hostname;
  const parts = host.split(".");
  // garabato.miniddo.com → ["garabato", "miniddo", "com"], tenant = garabato
  // miniddo.com         → ["miniddo", "com"], sin tenant
  // localhost           → ["localhost"], sin tenant
  if (parts.length >= 3 && parts.slice(-2).join(".") === "miniddo.com") {
    return parts[0];
  }
  return null;
}

// Request interceptor: attach JWT token + X-Tenant header
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Identifica el tenant al backend (necesario en deploys multi-host:
  // frontend Vercel en garabato.miniddo.com + backend Railway en api.miniddo.com)
  const tenantSlug = detectTenantSlug();
  if (tenantSlug) {
    config.headers["X-Tenant"] = tenantSlug;
  }
  return config;
});

// Response interceptor: handle 401 with token refresh queue
let isRefreshing = false;
let refreshQueue = [];

function processQueue(error, token = null) {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  refreshQueue = [];
}

// Endpoints donde NO queremos la logica de refresh (login/refresh mismos)
const SKIP_401_INTERCEPTOR = ["/auth/token/", "/auth/token/refresh/"];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si el 401 viene del endpoint de login mismo, no intentamos refresh ni redirigimos
    const requestUrl = originalRequest?.url || "";
    const isAuthEndpoint = SKIP_401_INTERCEPTOR.some((u) => requestUrl.includes(u));

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
        return Promise.reject(error);
      }

      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      isRefreshing = true;

      try {
        const { data } = await axios.post(`${API_BASE}/api/v1/auth/token/refresh/`, {
          refresh: refreshToken,
        });
        localStorage.setItem("access_token", data.access);
        if (data.refresh) {
          localStorage.setItem("refresh_token", data.refresh);
        }
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        processQueue(null, data.access);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
