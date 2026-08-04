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

export const getAdminCreditFactors = async () => (await API.get("/v1/admin/credit-factors")).data;
export const updateAdminCreditFactor = async (category, creditRate, co2Factor) =>
  (
    await API.patch(`/v1/admin/credit-factors/${category}`, {
      credit_rate: creditRate,
      co2_factor: co2Factor,
    })
  ).data;

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

// ── Manager: Batch Management ────────────────────────────────────────────
export const getManagerBatches = async () => (await API.get("/v1/manager/batches")).data;
export const getManagerRecyclers = async () => (await API.get("/v1/manager/recyclers")).data;
export const assignManagerBatch = async (batchId, recyclerId) =>
  (
    await API.post(`/v1/manager/batches/${batchId}/assign`, {
      recycler_id: recyclerId,
    })
  ).data;

// ── Recycler: Batches ─────────────────────────────────────────────────
export const getRecyclerBatches = async () => (await API.get("/v1/recycler/batches")).data;
export const acceptRecyclerBatch = async (batchId) =>
  (await API.post(`/v1/recycler/batches/${batchId}/accept`)).data;
export const rejectRecyclerBatch = async (batchId, note) =>
  (await API.post(`/v1/recycler/batches/${batchId}/reject`, { note })).data;
export const processRecyclerBatch = async (batchId) =>
  (await API.post(`/v1/recycler/batches/${batchId}/process`)).data;
export const listRecyclerNotifications = async () =>
  (await API.get("/v1/recycler/notifications")).data;
export const markRecyclerNotificationRead = async (notificationId) =>
  (await API.patch(`/v1/recycler/notifications/${notificationId}/read`)).data;
export const markAllRecyclerNotificationsRead = async () =>
  (await API.patch("/v1/recycler/notifications/read")).data;

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

export const getPublicTracking = async (reference) => {
  const { data } = await API.get(
    `/v1/track/${encodeURIComponent(reference.trim())}?t=${Date.now()}`
  );
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

export const markAllUserNotificationsRead = async () => {
  const { data } = await API.patch("/v1/user/notifications/read");
  return data;
};

export const getCollectorRoute = async () => (await API.get("/v1/collector/route")).data;
export const completeCollectorStop = async (stopId) =>
  (await API.post(`/v1/collector/stops/${stopId}/complete`)).data;
export const undoCollectorStop = async (stopId) =>
  (await API.post(`/v1/collector/stops/${stopId}/undo`)).data;
export const notifyCollectorStop = async (stopId, payload) =>
  (await API.post(`/v1/collector/stops/${stopId}/notify`, payload)).data;
export const flagCollectorStop = async (stopId, payload) =>
  (await API.post(`/v1/collector/stops/${stopId}/flag`, payload)).data;
export const markCollectorStopClean = async (stopId) =>
  (await API.post(`/v1/collector/stops/${stopId}/clean`)).data;
export const listCollectorNotifications = async () =>
  (await API.get("/v1/collector/notifications")).data;
export const markCollectorNotificationRead = async (notificationId) =>
  (await API.patch(`/v1/collector/notifications/${notificationId}/read`)).data;
export const markAllCollectorNotificationsRead = async () =>
  (await API.patch("/v1/collector/notifications/read")).data;
export const getCompletedCollectorCollections = async () =>
  (await API.get("/v1/collector/completed-collections")).data;

// ── Civic Reuse Exchange (Community Shelf) ──────────────────────────────────
export const listCommunityShelf = async (params) =>
  (await API.get("/v1/reuse/shelf", { params })).data;

export const listMyDonations = async () => (await API.get("/v1/reuse/donations/my")).data;

export const createDonation = async (payload) =>
  (await API.post("/v1/reuse/donations", payload)).data;

export const withdrawDonation = async (listingId) =>
  (await API.post(`/v1/reuse/donations/${listingId}/withdraw`)).data;

export const claimDonation = async (listingId) =>
  (await API.post(`/v1/reuse/donations/${listingId}/claim`)).data;

export const listMyClaims = async (filter = "") =>
  (await API.get("/v1/reuse/claims/my", { params: { filter } })).data;

// Manager Review endpoints
export const getManagerPendingDonations = async () =>
  (await API.get("/v1/reuse/manager/donations/pending")).data;

export const getManagerPendingClaims = async () =>
  (await API.get("/v1/reuse/manager/claims/pending")).data;

export const getManagerAllDonations = async () =>
  (await API.get("/v1/reuse/manager/donations")).data;

export const reviewManagerDonation = async (listingId, payload) =>
  (await API.post(`/v1/reuse/donations/${listingId}/review`, payload)).data;

export const reviewManagerClaim = async (claimId, payload) =>
  (await API.post(`/v1/reuse/claims/${claimId}/review`, payload)).data;
