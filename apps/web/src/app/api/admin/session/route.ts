import { NextResponse } from "next/server";

const COOKIE_NAME = "atoz_admin_access_token";

export async function DELETE() {
  const response = NextResponse.json({ ok: true });
  response.cookies.set(COOKIE_NAME, "", {
    httpOnly: true,
    secure: true,
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  return response;
}

export { COOKIE_NAME };
