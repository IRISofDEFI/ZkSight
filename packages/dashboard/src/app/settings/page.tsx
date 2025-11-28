// src/app/settings/page.tsx
"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Bell, Database, Zap, Shield, Settings as SettingsIcon } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto px-8 py-8 bg-gradient-to-br from-black via-zinc-950/50 to-black">
          {/* Page Title */}
          <div className="mb-12">
            <div className="flex items-center gap-5">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-slate-600 to-slate-800 flex items-center justify-center border border-slate-700">
                <SettingsIcon className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-5xl font-black tracking-tighter">Settings</h1>
                <p className="text-xl text-zinc-400 mt-2">Configure system preferences and integrations</p>
              </div>
            </div>
          </div>

          {/* Settings Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
            {/* Notifications */}
            <div className="bg-zinc-900/70 backdrop-blur-2xl rounded-3xl p-8 border border-blue-500/30 shadow-2xl">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-2xl bg-blue-500/20 border border-blue-500/40 flex items-center justify-center">
                  <Bell className="w-7 h-7 text-blue-400" />
                </div>
                <h3 className="text-2xl font-black text-blue-300">Notifications</h3>
              </div>

              <div className="space-y-5">
                <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                  <span className="font-medium">Email Alerts</span>
                  <Toggle enabled />
                </div>
                <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                  <span className="font-medium">Query Completion</span>
                  <Toggle enabled />
                </div>
                <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                  <span className="font-medium">Anomaly Detection</span>
                  <Toggle enabled={false} />
                </div>
              </div>
            </div>

            {/* Data Sources */}
            <div className="bg-zinc-900/70 backdrop-blur-2xl rounded-3xl p-8 border border-green-500/30 shadow-2xl">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-2xl bg-green-500/20 border border-green-500/40 flex items-center justify-center">
                  <Database className="w-7 h-7 text-green-400" />
                </div>
                <h3 className="text-2xl font-black text-green-300">Data Sources</h3>
              </div>

              <div className="space-y-5">
                <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                  <span className="font-medium">Zcash Node URL</span>
                  <input
                    type="text"
                    defaultValue="https://mainnet.z.cash"
                    className="w-64 px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-sm focus:outline-none focus:border-green-500/50 transition-all"
                  />
                </div>
                <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                  <span className="font-medium">API Refresh Rate</span>
                  <input
                    type="text"
                    defaultValue="30s"
                    className="w-32 px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-sm text-center focus:outline-none focus:border-green-500/50 transition-all"
                  />
                </div>
              </div>
            </div>

            {/* Performance */}
            <div className="bg-zinc-900/70 backdrop-blur-2xl rounded-3xl p-8 border border-amber-500/30 shadow-2xl">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
                  <Zap className="w-7 h-7 text-amber-400" />
                </div>
                <h3 className="text-2xl font-black text-amber-300">Performance</h3>
              </div>

              <div className="space-y-5">
                <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                  <span className="font-medium">Cache Duration</span>
                  <input
                    type="text"
                    defaultValue="5 minutes"
                    className="w-40 px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-sm text-center focus:outline-none focus:border-amber-500/50 transition-all"
                  />
                </div>
                <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                  <span className="font-medium">Max Concurrent Agents</span>
                  <input
                    type="text"
                    defaultValue="7"
                    className="w-24 px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-sm text-center focus:outline-none focus:border-amber-500/50 transition-all"
                  />
                </div>
              </div>
            </div>

            {/* Security */}
            <div className="bg-zinc-900/70 backdrop-blur-2xl rounded-3xl p-8 border border-purple-500/30 shadow-2xl">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-2xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center">
                  <Shield className="w-7 h-7 text-purple-400" />
                </div>
                <h3 className="text-2xl font-black text-purple-300">Security</h3>
              </div>

              <div className="space-y-5">
                <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                  <span className="font-medium">Two-Factor Auth</span>
                  <Toggle enabled />
                </div>
                <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                  <span className="font-medium">Session Timeout</span>
                  <input
                    type="text"
                    defaultValue="30 minutes"
                    className="w-40 px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-sm text-center focus:outline-none focus:border-purple-500/50 transition-all"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button className="px-10 py-4 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 rounded-2xl font-bold text-lg shadow-lg shadow-blue-500/30 transition-all hover:scale-105 active:scale-95">
              Save Changes
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}

// Reusable Toggle Component (pure Tailwind + React)
function Toggle({ enabled = true }: { enabled?: boolean }) {
  return (
    <div
      className={`relative w-14 h-8 rounded-full transition-all cursor-pointer ${
        enabled ? "bg-blue-500" : "bg-zinc-700"
      }`}
    >
      <div
        className={`absolute top-1 w-6 h-6 bg-white rounded-full transition-transform shadow-md ${
          enabled ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </div>
  );
}