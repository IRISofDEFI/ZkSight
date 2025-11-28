// src/app/dashboard/page.tsx
"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Zap, Activity, Database, Users, Clock, TrendingUp } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts";
import ProtectedRoute from "@/components/ProtectedRoute";

const txData = [
  { time: "00:00", value: 1800 },
  { time: "04:00", value: 3200 },
  { time: "08:00", value: 2800 },
  { time: "12:00", value: 4900 },
  { time: "16:00", value: 4200 },
  { time: "20:00", value: 5800 },
  { time: "23:59", value: 5500 },
];

const hashData = [
  { time: "00:00", value: 7200 },
  { time: "04:00", value: 7800 },
  { time: "08:00", value: 8200 },
  { time: "12:00", value: 9800 },
  { time: "16:00", value: 9500 },
  { time: "20:00", value: 9900 },
  { time: "23:59", value: 10000 },
];

const recentQueries = [
  { title: "Transaction volume trends over 30 days", time: "2 min ago", accuracy: "98.5%" },
  { title: "Network hashrate anomaly detection", time: "15 min ago", accuracy: "97.2%" },
  { title: "Block time distribution analysis", time: "1 hour ago", accuracy: "99.1%" },
];

export default function DashboardPage() {
  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto px-8 py-8 bg-gradient-to-br from-black via-zinc-950/50 to-black">
          {/* MISSION CONTROL */}
          <div className="mb-12">
            <h1 className="text-7xl font-black tracking-tighter bg-gradient-to-r from-blue-400 via-purple-400 to-amber-400 bg-clip-text text-transparent">
              MISSION CONTROL
            </h1>
            <p className="text-xl text-zinc-400 mt-3">Real-time Multi-Agent Intelligence System • Zcash Network Analytics</p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-10">
            {/* Network Hashrate */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-900/40 to-blue-950/60 backdrop-blur-2xl border border-blue-500/30 p-8 shadow-2xl">
              <div className="flex justify-between items-start mb-6">
                <Zap className="w-10 h-10 text-blue-400" />
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 border border-green-500/40 text-green-400 text-xs font-bold">
                  <TrendingUp className="w-4 h-4" /> +12.5%
                </div>
              </div>
              <p className="text-sm uppercase tracking-wider text-zinc-400 mb-2">Network Hashrate</p>
              <h2 className="text-6xl font-black text-blue-400 mb-6">8.2 <span className="text-2xl text-zinc-500">GH/s</span></h2>
              <div className="flex gap-1 h-12 items-end">
                {[70, 80, 75, 88, 95, 100, 92].map((h, i) => (
                  <div key={i} className="flex-1 bg-blue-500/30 rounded-t" style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>

            {/* Active Queries */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-amber-900/40 to-amber-950/60 backdrop-blur-2xl border border-amber-500/30 p-8 shadow-2xl">
              <div className="flex justify-between items-start mb-6">
                <Activity className="w-10 h-10 text-amber-400" />
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 border border-green-500/40 text-green-400 text-xs font-bold">
                  <TrendingUp className="w-4 h-4" /> +8.3%
                </div>
              </div>
              <p className="text-sm uppercase  uppercase tracking-wider text-zinc-400 mb-2">Active Queries</p>
              <h2 className="text-6xl font-black text-amber-400">142</h2>
            </div>

            {/* Blocks Analyzed */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-green-900/40 to-green-950/60 backdrop-blur-2xl border border-green-500/30 p-8 shadow-2xl">
              <div className="flex justify-between items-start mb-6">
                <Database className="w-10 h-10 text-green-400" />
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 border border-green-500/40 text-green-400 text-xs font-bold">
                  <TrendingUp className="w-4 h-4" /> +15.2%
                </div>
              </div>
              <p className="text-sm uppercase tracking-wider text-zinc-400 mb-2">Blocks Analyzed</p>
              <h2 className="text-6xl font-black text-green-400">2.4M</h2>
            </div>

            {/* Active Agents */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-purple-900/40 to-purple-950/60 backdrop-blur-2xl border border-purple-500/30 p-8 shadow-2xl">
              <div className="flex justify-between items-start mb-6">
                <Users className="w-10 h-10 text-purple-400" />
                <span className="text-zinc-400 text-sm font-bold">+0%</span>
              </div>
              <p className="text-sm uppercase tracking-wider text-zinc-400 mb-2">Active Agents</p>
              <h2 className="text-6xl font-black text-purple-400">7</h2>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-10">
            {/* Transaction Activity */}
            <div className="bg-zinc-900/70 backdrop-blur-2xl rounded-3xl p-8 border border-white/10">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="text-2xl font-black text-white">Transaction Activity</h3>
                  <p className="text-sm text-zinc-400">24-hour volume analysis</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-green-400 text-xs font-bold">LIVE</span>
                </div>
              </div>
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={txData}>
                    <defs>
                      <linearGradient id="txFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#8B5CF6" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#8B5CF6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#27272a" strokeDasharray="4 4" />
                    <XAxis dataKey="time" stroke="#52525b" tick={{ fill: "#71717a" }} />
                    <YAxis stroke="#52525b" tick={{ fill: "#71717a" }} />
                    <Area type="monotone" dataKey="value" stroke="#8B5CF6" strokeWidth={3} fill="url(#txFill)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Network Hashrate */}
            <div className="bg-zinc-900/70 backdrop-blur-2xl rounded-3xl p-8 border border-white/10">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="text-2xl font-black text-white">Network Hashrate</h3>
                  <p className="text-sm text-zinc-400">Computational power distribution</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-green-400 text-xs font-bold">LIVE</span>
                </div>
              </div>
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={hashData}>
                    <defs>
                      <linearGradient id="hashFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#27272a" strokeDasharray="4 4" />
                    <XAxis dataKey="time" stroke="#52525b" tick={{ fill: "#71717a" }} />
                    <YAxis stroke="#52525b" tick={{ fill: "#71717a" }} />
                    <Area type="monotone" dataKey="value" stroke="#60A5FA" strokeWidth={3} fill="url(#hashFill)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Agent Network + Recent Queries */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            {/* Agent Network */}
            <div className="bg-zinc-900/70 backdrop-blur-2xl rounded-3xl p-8 border border-purple-500/20">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-2xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center">
                  <Activity className="w-7 h-7 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-black text-purple-300">Agent Network</h3>
                  <p className="text-sm text-zinc-400">Real-time communication mesh</p>
                </div>
              </div>

              <div className="relative h-96 bg-black/50 rounded-3xl border border-purple-500/10 overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative">
                    <div className="absolute inset-0 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 blur-3xl opacity-70" />
                    <div className="w-32 h-32 rounded-full border-4 border-purple-500/50 animate-pulse" />
                    <div className="absolute inset-4 rounded-full bg-black/80 backdrop-blur-md border border-purple-400/60 flex items-center justify-center">
                      <Activity className="w-16 h-16 text-purple-400" />
                    </div>
                  </div>
                </div>

                <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-8 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-green-400" />
                    <span className="text-zinc-400 uppercase tracking-wider">Active</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-amber-400" />
                    <span className="text-zinc-400 uppercase tracking-wider">Processing</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-zinc-600" />
                    <span className="text-zinc-400 uppercase tracking-wider">Idle</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Query Activity */}
            <div className="bg-zinc-900/70 backdrop-blur-2xl rounded-3xl p-8 border border-amber-500/20">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
                  <Clock className="w-7 h-7 text-amber-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-black text-amber-300">Recent Query Activity</h3>
                  <p className="text-sm text-zinc-400">Latest analysis requests</p>
                </div>
              </div>

              <div className="space-y-5">
                {recentQueries.map((q, i) => (
                  <div key={i} className="group bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:border-green-500/40 transition-all cursor-pointer">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-5">
                        <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse shadow-lg shadow-green-400/50" />
                        <div>
                          <p className="font-semibold text-white group-hover:text-green-300 transition-colors">{q.title}</p>
                          <p className="text-xs text-zinc-400 mt-1">
                            {q.time} • Accuracy: <span className="text-green-400">{q.accuracy}</span>
                          </p>
                        </div>
                      </div>
                      <div className="px-5 py-2 rounded-full bg-green-500/20 border border-green-500/40 text-green-400 text-xs font-bold">
                        COMPLETED
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}





// src/app/dashboard/page.tsx