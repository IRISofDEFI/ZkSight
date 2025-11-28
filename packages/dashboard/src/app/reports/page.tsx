// src/app/reports/page.tsx
"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Activity, Clock } from "lucide-react";

const recentQueries = [
  {
    title: "Transaction volume trends over 30 days",
    time: "2 min ago",
    accuracy: "98.5%",
  },
  {
    title: "Network hashrate anomaly detection",
    time: "15 min ago",
    accuracy: "97.2%",
  },
  {
    title: "Block time distribution analysis",
    time: "1 hour ago",
    accuracy: "99.1%",
  },
  {
    title: "Shielded pool usage patterns",
    time: "3 hours ago",
    accuracy: "96.8%",
  },
  {
    title: "Miner concentration risk assessment",
    time: "6 hours ago",
    accuracy: "98.2%",
  },
];

export default function ReportsPage() {
  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto px-8 py-8">
          {/* Header */}
          <div className="mb-12">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-[0_0_40px_rgba(147,51,234,0.6)]">
                <Activity className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-5xl font-black tracking-tight">Reports</h1>
                <p className="text-gray-400 text-xl mt-1">Complete analysis history and exported intelligence</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {/* Left Column: Agent Network Mesh */}
            <div className="xl:col-span-2">
              <div className="glass-card rounded-3xl p-8 border border-purple-500/20 relative overflow-hidden">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
                    <Activity className="w-6 h-6 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-purple-300">Agent Network</h3>
                    <p className="text-sm text-gray-400 font-mono">Real-time communication mesh</p>
                  </div>
                </div>

                {/* Mesh Visualization */}
                <div className="relative h-96 rounded-2xl overflow-hidden bg-black/40 border border-purple-500/20">
                  <svg className="absolute inset-0 w-full h-full" viewBox="0 0 800 400">
                    <defs>
                      <linearGradient id="meshGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.6" />
                        <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.6" />
                      </linearGradient>
                    </defs>

                    {/* Animated Connections */}
                    <line x1="200" y1="200" x2="600" y2="100" stroke="url(#meshGradient)" strokeWidth="2" opacity="0.7">
                      <animate attributeName="stroke-dashoffset" from="0" to="-100" dur="8s" repeatCount="indefinite" />
                    </line>
                    <line x1="200" y1="200" x2="600" y2="300" stroke="url(#meshGradient)" strokeWidth="2" opacity="0.7">
                      <animate attributeName="stroke-dashoffset" from="0" to="-100" dur="10s" repeatCount="indefinite" />
                    </line>
                    <line x1="400" y1="50" x2="400" y2="350" stroke="url(#meshGradient)" strokeWidth="2" opacity="0.5">
                      <animate attributeName="stroke-dashoffset" from="0" to="-100" dur="12s" repeatCount="indefinite" />
                    </line>
                  </svg>

                  {/* Central Core */}
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 shadow-2xl shadow-purple-500/50 flex items-center justify-center animate-pulse">
                      <div className="w-16 h-16 rounded-full bg-black/60 flex items-center justify-center border-2 border-purple-400">
                        <Activity className="w-8 h-8 text-purple-300" />
                      </div>
                    </div>
                  </div>

                  {/* Agent Nodes */}
                  {[
                    { x: 15, y: 20, name: "Query", color: "green" },
                    { x: 70, y: 15, name: "Data", color: "amber" },
                    { x: 85, y: 70, name: "Analysis", color: "green" },
                    { x: 50, y: 85, name: "Narrative", color: "slate" },
                    { x: 20, y: 70, name: "Fact-Checker", color: "green" },
                    { x: 35, y: 30, name: "Follow-up", color: "amber" },
                    { x: 80, y: 40, name: "Monitoring", color: "green" },
                  ].map((node, i) => (
                    <div
                      key={i}
                      className="absolute"
                      style={{ left: `${node.x}%`, top: `${node.y}%`, transform: "translate(-50%, -50%)" }}
                    >
                      <div className={`w-14 h-14 rounded-2xl glass-card border border-${node.color}-500/50 flex flex-col items-center justify-center group cursor-pointer hover:scale-110 transition-all`}>
                        <div className={`w-3 h-3 rounded-full bg-${node.color}-500 ${node.color === "amber" ? "animate-pulse" : ""} shadow-lg shadow-${node.color}-500/50`} />
                        <span className="text-xs font-bold font-mono mt-1">{node.name}</span>
                      </div>
                    </div>
                  ))}

                  {/* Legend */}
                  <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-6">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-green-500" />
                      <span className="text-xs text-gray-400 font-mono uppercase">Active</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-amber-500 animate-pulse" />
                      <span className="text-xs text-gray-400 font-mono uppercase">Processing</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-slate-500" />
                      <span className="text-xs text-gray-400 font-mono uppercase">Idle</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Recent Query Activity */}
            <div>
              <div className="glass-card rounded-3xl p-8 border border-amber-500/20">
                <div className="flex items-center gap-3 mb-8">
                  <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-amber-400" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-amber-300">Recent Query Activity</h3>
                    <p className="text-sm text-gray-400 font-mono">Latest analysis requests</p>
                  </div>
                </div>

                <div className="space-y-4">
                  {recentQueries.map((query, i) => (
                    <div
                      key={i}
                      className="glass-card rounded-2xl p-6 border border-white/10 hover:border-amber-500/30 transition-all duration-300 cursor-pointer group relative overflow-hidden"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                      
                      <div className="relative flex items-center justify-between">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="w-3 h-3 rounded-full bg-green-400 shadow-lg shadow-green-400/50 animate-pulse" />
                          <div>
                            <p className="font-bold text-base group-hover:text-amber-300 transition-colors">
                              {query.title}
                            </p>
                            <p className="text-xs text-gray-400 font-mono mt-1">
                              {query.time} • Accuracy: <span className="text-green-400">{query.accuracy}</span>
                            </p>
                          </div>
                        </div>
                        <div className="px-4 py-2 rounded-xl bg-green-500/20 border border-green-500/30 text-green-400 text-xs font-bold font-mono">
                          COMPLETED
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}