const serviceUrl = () => (process.env.RAG_SERVICE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function proxy(request, { params }) {
  const path = (await params).path.join("/");
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer();
  try {
    const upstream = await fetch(`${serviceUrl()}/${path}`, {
      method: request.method,
      headers,
      body,
      signal: AbortSignal.timeout(120000)
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: { "content-type": upstream.headers.get("content-type") || "application/json" }
    });
  } catch (error) {
    console.error("RAG service unavailable:", error instanceof Error ? error.message : error);
    return Response.json({ detail: "The RAG service is unavailable. Start the Python service and try again." }, { status: 503 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
