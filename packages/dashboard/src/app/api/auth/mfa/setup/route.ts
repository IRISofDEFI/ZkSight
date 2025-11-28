import { NextResponse } from "next/server";
import speakeasy from "speakeasy";
import QRCode from "qrcode";

export async function POST(req: Request) {
  try {
    // Generate secret
    const secret = speakeasy.generateSecret({
      name: "Chimera Analytics",
      issuer: "Chimera",
      length: 32,
    });

    // Generate QR code
    const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url || "");

    return NextResponse.json({
      secret: secret.base32,
      qrCode: qrCodeUrl,
    });
  } catch (error) {
    console.error("MFA setup error:", error);
    return NextResponse.json(
      { error: "Failed to setup MFA" },
      { status: 500 }
    );
  }
}
