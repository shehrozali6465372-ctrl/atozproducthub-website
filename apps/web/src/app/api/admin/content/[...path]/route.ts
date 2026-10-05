import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const COOKIE_NAME = "atoz_admin_access_token";

function contentApiBase() {
  return (
    process.env.CONTENT_API_BASE_URL ??
    process.env.NEXT_PUBLIC_CONTENT_API_BASE_URL ??
    ""
  ).replace(/\/$/, "");
}

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const token = (await cookies()).get(COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ error: "Admin authentication required." }, { status: 401 });
  }

  const base = contentApiBase();
  if (!base) {
    return NextResponse.json({ error: "Content API is not configured." }, { status: 503 });
  }

  const { path } = await context.params;
  const target = `${base}/api/v1/admin/${path.join("/")}`;
  const incoming = new URL(request.url);
  const query = incoming.search;
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token}`);
  headers.set("Accept", "application/json");
  const nicheId = request.headers.get("X-Niche-Id");
  if (nicheId) headers.set("X-Niche-Id", nicheId);
  if (request.headers.get("Content-Type")) {
    headers.set("Content-Type", request.headers.get("Content-Type")!);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };
  if (!["GET", "HEAD"].includes(request.method)) {
    init.body = await request.arrayBuffer();
  }

  const upstream = await fetch(`${target}${query}`, init);
  const responseHeaders = new Headers();
  const contentType = upstream.headers.get("content-type");
  if (contentType) responseHeaders.set("content-type", contentType);

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
