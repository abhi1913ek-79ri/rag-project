export async function apiRequest(path, options = {}) {
  const response = await fetch(`/api${path}`, options);
  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error("The server returned an invalid response.");
  }
  if (!response.ok) throw new Error(data.detail || "The request could not be completed.");
  return data;
}

export const documentsApi = {
  list: () => apiRequest("/documents"),
  upload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return apiRequest("/upload", { method: "POST", body: form });
  },
  remove: (id) => apiRequest(`/documents/${encodeURIComponent(id)}`, { method: "DELETE" }),
  audit: (query, documentId) => apiRequest("/audit", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ query, document_id: documentId })
  }),
  summarize: (documentId, force = false) => apiRequest("/summarize", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ document_id: documentId, force })
  })
};
