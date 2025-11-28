"use client";

import { useSession } from "next-auth/react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Shield, CheckCircle } from "lucide-react";
import { toast } from "sonner";

export default function MFAPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [code, setCode] = useState("");
  const [qrCode, setQrCode] = useState("");
  const [secret, setSecret] = useState("");
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Generate MFA secret and QR code
    async function setupMFA() {
      try {
        const response = await fetch("/api/auth/mfa/setup", {
          method: "POST",
        });
        
        if (response.ok) {
          const data = await response.json();
          setSecret(data.secret);
          setQrCode(data.qrCode);
        }
      } catch (error) {
        toast.error("Failed to setup MFA");
      }
    }

    if (!enabled) {
      setupMFA();
    }
  }, [enabled]);

  const verifyCode = async () => {
    if (code.length !== 6) {
      toast.error("Please enter a 6-digit code");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/auth/mfa/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, secret }),
      });

      if (response.ok) {
        setEnabled(true);
        toast.success("MFA enabled successfully!");
        setTimeout(() => router.push("/dashboard"), 2000);
      } else {
        toast.error("Invalid code. Please try again.");
        setCode("");
      }
    } catch (error) {
      toast.error("Verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
      <Card className="bg-neutral-900 p-10 rounded-xl w-full max-w-md border border-neutral-800">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center">
            <Shield className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Two-Factor Authentication</h1>
            <p className="text-neutral-400 text-sm">Secure your account</p>
          </div>
        </div>

        {!enabled ? (
          <>
            <div className="mb-6">
              <p className="text-neutral-300 mb-4">
                Scan this QR code with your authenticator app:
              </p>
              <p className="text-sm text-neutral-500 mb-4">
                Recommended apps: Google Authenticator, Authy, Microsoft Authenticator
              </p>
              
              {qrCode ? (
                <div className="bg-white p-4 rounded-xl inline-block">
                  <img src={qrCode} alt="QR Code" className="w-64 h-64" />
                </div>
              ) : (
                <div className="w-64 h-64 bg-neutral-800 rounded-xl flex items-center justify-center">
                  <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
                </div>
              )}
            </div>

            <div className="mb-6">
              <p className="text-sm text-neutral-400 mb-2">
                Or enter this code manually:
              </p>
              <code className="block bg-neutral-800 p-3 rounded-lg text-center font-mono text-purple-400 select-all">
                {secret || "Loading..."}
              </code>
            </div>

            <div className="mb-6">
              <label className="block text-sm text-neutral-400 mb-2">
                Enter the 6-digit code from your app:
              </label>
              <Input
                type="text"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                placeholder="000000"
                className="text-center text-2xl tracking-widest bg-neutral-800 border-neutral-700"
                disabled={loading}
              />
            </div>

            <Button
              onClick={verifyCode}
              disabled={code.length !== 6 || loading}
              className="w-full bg-purple-600 hover:bg-purple-700 py-6 text-lg font-semibold"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Verifying...
                </div>
              ) : (
                "Enable MFA"
              )}
            </Button>
          </>
        ) : (
          <div className="text-center py-8">
            <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-green-400 mb-2">
              MFA Enabled Successfully!
            </h2>
            <p className="text-neutral-400 mb-6">
              Your account is now protected with two-factor authentication.
            </p>
            <Button
              onClick={() => router.push("/dashboard")}
              className="bg-purple-600 hover:bg-purple-700"
            >
              Go to Dashboard
            </Button>
          </div>
        )}

        <div className="mt-6 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
          <p className="text-xs text-blue-300">
            <strong>Important:</strong> Save your backup codes in a safe place. You'll need them if you lose access to your authenticator app.
          </p>
        </div>
      </Card>
    </div>
  );
}
