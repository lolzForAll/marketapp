const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  getSellerProfile: () => request("/seller-profile"),
  updateSellerProfile: (data) =>
    request("/seller-profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  listItems: () => request("/items"),
  getItem: (id) => request(`/items/${id}`),
  createItem: (title, files) => {
    const form = new FormData();
    form.append("title", title || "");
    for (const file of files) form.append("files", file);
    return request("/items", { method: "POST", body: form });
  },
  addPhotos: (id, files) => {
    const form = new FormData();
    for (const file of files) form.append("files", file);
    return request(`/items/${id}/photos`, { method: "POST", body: form });
  },
  updateItem: (id, data) =>
    request(`/items/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
  deleteItem: (id) => request(`/items/${id}`, { method: "DELETE" }),
  analyzeItem: (id) => request(`/items/${id}/analyze`, { method: "POST" }),
  selectMatch: (id, payload) =>
    request(`/items/${id}/select-match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  generateListing: (id) => request(`/items/${id}/generate-listing`, { method: "POST" }),
  approveItem: (id) => request(`/items/${id}/approve`, { method: "POST" }),
  publishAssist: (id) => request(`/items/${id}/publish-assist`, { method: "POST" }),
  markPublished: (id) => request(`/items/${id}/mark-published`, { method: "POST" }),
};
