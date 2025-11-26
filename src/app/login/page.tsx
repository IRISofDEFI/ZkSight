"use client";

import { signIn } from "next-auth/react";
import Link from "next/link";
import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleLogin(e: any) {
    e.preventDefault();

    await signIn("credentials", {
      email,
      password,
      callbackUrl: "/dashboard",
    });
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-black text-white">
      <div className="p-8 rounded-xl bg-neutral-900 shadow-xl w-[350px]">
        <h1 className="text-3xl font-bold mb-6">Login</h1>

        <form onSubmit={handleLogin} className="space-y-4">
          <input
            className="w-full p-3 rounded bg-neutral-800 border border-neutral-700 focus:border-purple-500 outline-none transition"
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

          <button className="w-full bg-purple-600 py-3 rounded font-semibold hover:bg-purple-700 transition">
            Login
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

        {/* ←←← This is the part you asked for */}
        <p className="text-center mt-8 text-neutral-400">
          Don't have an account?{" "}
          <Link href="/signup" className="text-purple-500 hover:underline font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}