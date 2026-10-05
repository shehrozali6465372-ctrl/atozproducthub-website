import { NextResponse } from "next/server";

const API_BASE = process.env.ATOZ_API_BASE_URL ?? "https://atozproducthub-api.onrender.com";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const username = typeof body?.username === "string" ? body.username.trim() : "";
  const password = typeof body?.password === "string" ? body.password : "";
  if (!username || !password) {
    return NextResponse.json({ error: "Username and password are required." }, { status: 400 });
  }

  const upstream = await fetch(`${API_BASE.replace(/\/$/, "")}/api/v1/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ username, password }),
    cache: "no-store",
  }).catch(() => null);

  if (!upstream) return NextResponse.json({ error: "Authentication service unavailable." }, { status: 502 });
  const data = await upstream.json().catch(() => null);
  if (!upstream.ok) return NextResponse.json({ error: "Invalid admin credentials." }, { status: upstream.status });

  const token = typeof data?.access_token === "string" ? data.access_token : typeof data?.token === "string" ? data.token : "";
  if (!token) return NextResponse.json({ error: "Authentication service returned no access token." }, { status: 502 });

  const response = NextResponse.json({ ok: true });
  response.cookies.set("atoz_admin_access_token", token, {
    httpOnly: true,
    secure: true,
    sameSite: "strict",
    path: "/",
    maxAge: 60 * 60 * 8,
  });
  return response;
}
