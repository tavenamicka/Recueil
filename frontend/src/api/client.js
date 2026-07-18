const API_BASE = "/api";

async function handleResponse(res) {
  if (!res.ok) {
    let detail = "Une erreur est survenue. Réessaie dans un instant.";
    try {
      const data = await res.json();
      if (data.detail) detail = data.detail;
    } catch {
      // pas de corps JSON exploitable, on garde le message par défaut
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

function toQueryString(params = {}) {
  const usable = Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== "")
  );
  return new URLSearchParams(usable).toString();
}

function postJson(path, body) {
  return fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(handleResponse);
}

// --- Authentification ---

export function login(email, password) {
  return postJson("/auth/login", { email, password });
}

export function registerAccount(email, password) {
  return postJson("/auth/register", { email, password });
}

export function logout() {
  return postJson("/auth/logout", {});
}

export function fetchMe() {
  return fetch(`${API_BASE}/auth/me`).then(handleResponse);
}

export function forgotPassword(email, newPassword) {
  return postJson("/auth/forgot-password", { email, new_password: newPassword });
}

// --- Administration ---

export function fetchUsers() {
  return fetch(`${API_BASE}/admin/users`).then(handleResponse);
}

export function approveUser(userId) {
  return fetch(`${API_BASE}/admin/users/${userId}/approve`, { method: "POST" }).then(handleResponse);
}

export function rejectUser(userId) {
  return fetch(`${API_BASE}/admin/users/${userId}/reject`, { method: "POST" }).then(handleResponse);
}

export function deleteUser(userId) {
  return fetch(`${API_BASE}/admin/users/${userId}`, { method: "DELETE" }).then(handleResponse);
}

export function fetchPasswordResets() {
  return fetch(`${API_BASE}/admin/password-resets`).then(handleResponse);
}

export function approvePasswordReset(resetId) {
  return fetch(`${API_BASE}/admin/password-resets/${resetId}/approve`, { method: "POST" }).then(handleResponse);
}

export function rejectPasswordReset(resetId) {
  return fetch(`${API_BASE}/admin/password-resets/${resetId}/reject`, { method: "POST" }).then(handleResponse);
}

export function fetchCategories() {
  return fetch(`${API_BASE}/categories`).then(handleResponse);
}

export function fetchLiens(params) {
  return fetch(`${API_BASE}/liens?${toQueryString(params)}`).then(handleResponse);
}

export function fetchMedias(params) {
  return fetch(`${API_BASE}/medias?${toQueryString(params)}`).then(handleResponse);
}

export function updateLien(lienId, payload) {
  return fetch(`${API_BASE}/liens/${lienId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(handleResponse);
}

export function updateLienCategorie(lienId, categorieId) {
  return updateLien(lienId, { categorie_id: categorieId });
}

export function updateLienFavori(lienId, favori) {
  return updateLien(lienId, { favori });
}

export function updateLienTitre(lienId, titrePage) {
  return updateLien(lienId, { titre_page: titrePage });
}

export function updateMedia(mediaId, payload) {
  return fetch(`${API_BASE}/medias/${mediaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(handleResponse);
}

export function updateMediaFavori(mediaId, favori) {
  return updateMedia(mediaId, { favori });
}

export function updateMediaFilename(mediaId, filename) {
  return updateMedia(mediaId, { filename });
}

export function createLien(url) {
  return postJson("/liens", { url });
}

export function deleteLien(lienId) {
  return fetch(`${API_BASE}/liens/${lienId}`, { method: "DELETE" }).then(handleResponse);
}

export function deleteMedia(mediaId) {
  return fetch(`${API_BASE}/medias/${mediaId}`, { method: "DELETE" }).then(handleResponse);
}

export function importTxt(file) {
  const form = new FormData();
  form.append("file", file);
  return fetch(`${API_BASE}/import/txt`, { method: "POST", body: form }).then(handleResponse);
}

export function importMedia(file) {
  const form = new FormData();
  form.append("file", file);
  return fetch(`${API_BASE}/import/media`, { method: "POST", body: form }).then(handleResponse);
}

export function fetchImportStatus(jobId) {
  return fetch(`${API_BASE}/import/txt/${jobId}`).then(handleResponse);
}
