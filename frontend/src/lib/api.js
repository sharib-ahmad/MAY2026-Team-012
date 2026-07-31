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

export const getAdminDashboard = async () => {
  const { data } = await API.get("/v1/admin/dashboard");
  return data;
};

export const getManagerDashboard = async () => {
  const { data } = await API.get("/v1/manager/dashboard");
  return data;
};

export const markManagerNotificationsRead = async () => {
  const { data } = await API.patch("/v1/manager/notifications/read");
  return data;
};

export const updateManagerComplaint = async (ticketId, payload) => {
  const { data } = await API.patch(`/v1/manager/tickets/${ticketId}`, payload);
  return data;
};

export const assignManagerBulkPickup = async (requestId, collectorId) => {
  const { data } = await API.post(`/v1/manager/bulk-pickups/${requestId}/assign`, {
    collector_id: collectorId,
  });
  return data;
};

export const updateManagerWorker = async (workerId, payload) => {
  const { data } = await API.patch(`/v1/manager/workers/${workerId}`, payload);
  return data;
};

export const deleteManagerWorker = async (workerId) => {
  await API.delete(`/v1/manager/workers/${workerId}`);
};

export const getWards = async () => {
  const { data } = await API.get("/v1/admin/ward");
  return data;
};

export const createWard = async (wardData) => {
  const { data } = await API.post("/v1/admin/ward", wardData);
  return data;
};

export const getLogs = async (limit = 100) => {
  const { data } = await API.get("/v1/admin/logs", { params: { limit } });
  return data;
};

export const createAccount = async (accountData) => {
  const { data } = await API.post("/v1/admin/account", accountData);
  return data;
};

export const getZones = async () => {
  const { data } = await API.get("/v1/zones");
  return data;
};
export const getUserDashboard = async () => {
  const { data } = await API.get("/v1/user/dashboard");
  return data;
};

export const getUserImpact = async () => {
  const { data } = await API.get("/v1/user/impact");
  return data;
};

export const getUserPickupOptions = async () => {
  const { data } = await API.get("/v1/user/pickup-options");
  return data;
};

export const listUserPickups = async () => {
  const { data } = await API.get("/v1/user/pickups");
  return data;
};

export const scheduleUserPickup = async (payload) => {
  const { data } = await API.post("/v1/user/pickups", payload);
  return data;
};

export const cancelUserPickup = async (pickupId) => {
  const { data } = await API.patch(`/v1/user/pickups/${pickupId}/cancel`);
  return data;
};

export const getUserPickupTracking = async (pickupId) => {
  const { data } = await API.get(`/v1/user/pickups/${pickupId}/tracking`);
  return data;
};

export const listUserTickets = async () => {
  const { data } = await API.get("/v1/user/tickets");
  return data;
};

export const createUserTicket = async (payload) => {
  const { data } = await API.post("/v1/user/tickets", payload);
  return data;
};

export const listUserDailyPickupSchedules = async () => {
  const { data } = await API.get("/v1/user/daily-pickup-schedules");
  return data;
};

export const listUserNotifications = async () => {
  const { data } = await API.get("/v1/user/notifications");
  return data;
};

export const markUserNotificationRead = async (notificationId) => {
  const { data } = await API.patch(`/v1/user/notifications/${notificationId}/read`);
  return data;
};
