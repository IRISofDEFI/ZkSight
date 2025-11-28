import { NextResponse } from "next/server";
import speakeasy from "speakeasy";

export async function POST(req: Request) {
  try {
    const { code, secret } = await req.json();

    if (!code || !secret) {
      return NextResponse.json(
        { error: "Code and secret are required" },
        { status: 400 }
      );
    }

    // Verify the token
    const verified = speakeasy.totp.verify({
      secret,
      encoding: "base32",
      token: code,
      window: 2, // Allow 2 time steps before/after for clock drift
    });

    if (verified) {
      // TODO: Save secret to user profile in database
      // For now, just return success
      return NextResponse.json({ success: true });
    } else {
      return NextResponse.json(
        { error: "Invalid code" },
        { status: 401 }
      );
    }
  } catch (error) {
    console.error("MFA verification error:", error);
    return NextResponse.json(
      { error: "Verification failed" },
      { status: 500 }
    );
  }
}
