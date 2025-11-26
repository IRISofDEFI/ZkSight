"use client";

import { useState } from "react";
import Link from "next/link";
import { signIn } from "next-auth/react";  // ←←← THIS WAS MISSING!!!

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    // We're using NextAuth Credentials to "register" by attempting login
    // If user doesn't exist → we create them automatically (see route.ts update below)
    const res = await signIn("credentials", {
      email,
      password,
      name,
      redirect: false, // Important: don't redirect automatically
      action: "signup", // Custom flag we'll check in [...nextauth]/route.ts
    });

    if (res?.ok) {
      // Success → go to dashboard
      window.location.href = "/dashboard";
    } else {
      setError("Something went wrong. Try again.");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black text-white">
      <div className="p-8 rounded-xl bg-neutral-900 shadow-xl w-[380px]">
        <h1 className="text-3xl font-bold mb-2">Create Account</h1>
        <p className="text-neutral-400 mb-6">Join Chimera Dashboard</p>

        <form onSubmit={handleSignup} className="space-y-4">
          <input
            className="w-full p-3 rounded bg-neutral-800 border border-neutral-700 focus:border-purple-500 outline-none transition"
            placeholder="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            className="w-full p-3 rounded bg-neutral-800 border border-neutral-700 focus:border-purple-500 outline-none transition"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="w-full p-3 rounded bg-neutral-800 border border-neutral-700 focus:border-purple-500 outline-none transition"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-purple-600 py-3 rounded font-semibold hover:bg-purple-700 transition disabled:opacity-70"
          >
            {loading ? "Creating Account..." : "Sign Up"}
          </button>
        </form>

        <div className="mt-6 space-y-3">
          <button
            onClick={() => signIn("google", { callbackUrl: "/dashboard" })}
            className="w-full bg-red-600 py-3 rounded font-medium hover:bg-red-700 transition flex items-center justify-center gap-3"
          >
            Continue with Google
          </button>

          <button
            onClick={() => signIn("github", { callbackUrl: "/dashboard" })}
            className="w-full bg-neutral-800 py-3 rounded font-medium hover:bg-neutral-700 transition flex items-center justify-center gap-3 border border-neutral-700"
          >
            Continue with GitHub
          </button>
        </div>

        <p className="text-center mt-6 text-neutral-400">
          Already have an account?{" "}
          <Link href="/login" className="text-purple-500 hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}