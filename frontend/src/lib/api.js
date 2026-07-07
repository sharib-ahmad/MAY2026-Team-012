import axios from "axios";

const API = axios.create({
  baseURL: "/api",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT on every request
API.interceptors.request.use((cfg) => {
  const raw = localStorage.getItem("gc_token");
  if (raw) {
    try {
      const { access_token } = JSON.parse(raw);
      cfg.headers.Authorization = `Bearer ${access_token}`;
    } catch {
      /* ignore */
    }
  }
  return cfg;
});

// Auto-refresh on 401
API.interceptors.response.use(
  (res) => res,
  async (err) => {
    const orig = err.config;
    if (err.response?.status === 401 && !orig._retry) {
      orig._retry = true;
      const raw = localStorage.getItem("gc_token");
      if (raw) {
        try {
          const { refresh_token } = JSON.parse(raw);
          const { data } = await axios.post("/api/auth/refresh", { refresh_token });
          const stored = JSON.parse(raw);
          localStorage.setItem("gc_token", JSON.stringify({ ...stored, ...data }));
          orig.headers.Authorization = `Bearer ${data.access_token}`;
          return API(orig);
        } catch {
          localStorage.removeItem("gc_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(err);
  }
);

export default API;
