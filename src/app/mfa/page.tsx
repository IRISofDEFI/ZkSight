"use client";

import { useSession } from "next-auth/react";
import { useState } from "react";

export default function MFAPage() {
  const { data: session } = useSession();
  const [code, setCode] = useState("");
  const [enabled, setEnabled] = useState(false);

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="bg-neutral-900 p-10 rounded-xl w-[400px]">
        <h1 className="text-3xl font-bold mb-6">Two-Factor Authentication</h1>

        {!enabled ? (
          <>
            <p className="text-neutral-300 mb-6">
              Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
            </p>
            <div className="bg-gray-200 border-2 border-dashed rounded-xl w-64 h-64 mx-auto mb-6" />
            <p className="text-sm text-neutral-500 text-center mb-6">
              Fake QR code — in real app use speakeasy + qrcode
            </p>
            <button
              onClick={() => setEnabled(true)}
              className="w-full bg-purple-600 py-3 rounded font-bold hover:bg-purple-700"
            >
              I’ve Scanned the Code
            </button>
          </>
        ) : (
          <>
            <p className="text-green-400 font-bold mb-6">MFA Enabled Successfully! ✅</p>
            <button
              onClick={() => window.location.href = "/dashboard"}
              className="w-full bg-purple-600 py-3 rounded font-bold"
            >
              Go to Dashboard
            </button>
          </>
        )}
      </div>
    </div>
  );
}