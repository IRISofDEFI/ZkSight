// src/app/agents/page.tsx
"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Activity, Brain, Database, FileText, CircleCheckBig, ArrowRight, Radar, Zap } from "lucide-react";

const agents = [
  {
    name: "Query Agent",
    icon: Brain,
    status: "Active",
    statusColor: "green",
    description: "Processes natural language queries and routes them to appropriate agents",
    tasks: "1,247",
    avgResponse: "0.3s",
    tags: ["NLP Processing", "Intent Recognition", "Query Routing"],
    gradient: "from-blue-500/20 to-blue-600/10",
    border: "border-blue-500/30",
    iconColor: "text-blue-400",
  },
  {
    name: "Data Retrieval Agent",
    icon: Database,
    status: "Active",
    statusColor: "green",
    description: "Fetches data from Zcash blockchain and external sources",
    tasks: "3,421",
    avgResponse: "1.2s",
    tags: ["Blockchain Scanning", "API Integration", "Data Caching"],
    gradient: "from-green-500/20 to-green-600/10",
    border: "border-green-500/30",
    iconColor: "text-green-400",
  },
  {
    name: "Analysis Agent",
    icon: Activity,
    status: "Active",
    statusColor: "green",
    description: "Performs statistical analysis and pattern recognition on data",
    tasks: "892",
    avgResponse: "2.1s",
    tags: ["Statistical Analysis", "Pattern Recognition", "Trend Detection"],
    gradient: "from-purple-500/20 to-purple-600/10",
    border: "border-purple-500/30",
    iconColor: "text-purple-400",
  },
  {
    name: "Narrative Agent",
    icon: FileText,
    status: "Idle",
    statusColor: "slate",
    description: "Generates human-readable reports and insights from analysis results",
    tasks: "634",
    avgResponse: "1.5s",
    tags: ["Report Generation", "Data Storytelling", "Visualization"],
    gradient: "from-amber-500/20 to-amber-600/10",
    border: "border-amber-500/30",
    iconColor: "text-amber-400",
  },
  {
    name: "Fact-Checker Agent",
    icon: CircleCheckBig,
    status: "Active",
    statusColor: "green",
    description: "Validates analysis results and ensures data accuracy",
    tasks: "1,567",
    avgResponse: "0.8s",
    tags: ["Data Validation", "Cross-referencing", "Quality Assurance"],
    gradient: "from-green-500/20 to-green-600/10",
    border: "border-green-500/30",
    iconColor: "text-green-400",
  },
  {
    name: "Follow-up Agent",
    icon: ArrowRight,
    status: "Processing",
    statusColor: "amber",
    description: "Generates follow-up queries for deeper analysis",
    tasks: "445",
    avgResponse: "1.0s",
    tags: ["Query Generation", "Deep Dive Analysis", "Contextual Learning"],
    gradient: "from-blue-500/20 to-blue-600/10",
    border: "border-blue-500/30",
    iconColor: "text-blue-400",
  },
  {
    name: "Monitoring Agent",
    icon: Radar,
    status: "Active",
    statusColor: "green",
    description: "Continuously monitors network for anomalies and alerts",
    tasks: "8,923",
    avgResponse: "0.1s",
    tags: ["Real-time Monitoring", "Anomaly Detection", "Alert Management"],
    gradient: "from-red-500/20 to-red-600/10",
    border: "border-red-500/30",
    iconColor: "text-red-400",
  },
];

export default function AgentsPage() {
  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto px-8 py-8">
          {/* Header */}
          <div className="mb-10">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-[0_0_40px_rgba(147,51,234,0.6)]">
                <Activity className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-5xl font-black tracking-tight">Agent Network</h1>
                <p className="text-gray-400 text-xl mt-1">Monitor and manage AI agents powering the analytics system</p>
              </div>
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            <div className="glass-effect rounded-2xl p-6 border border-green-500/30 bg-gradient-to-br from-green-500/20 to-green-600/10 backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Active Agents</p>
                  <h3 className="text-4xl font-bold">5</h3>
                </div>
                <Zap className="w-12 h-12 text-green-400" />
              </div>
            </div>
            <div className="glass-effect rounded-2xl p-6 border border-blue-500/30 bg-gradient-to-br from-blue-500/20 to-blue-600/10 backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Total Tasks</p>
                  <h3 className="text-4xl font-bold">17,129</h3>
                </div>
                <Activity className="w-12 h-12 text-blue-400" />
              </div>
            </div>
            <div className="glass-effect rounded-2xl p-6 border border-purple-500/30 bg-gradient-to-br from-purple-500/20 to-purple-600/10 backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Avg Response</p>
                  <h3 className="text-4xl font-bold">1.1s</h3>
                </div>
                <Brain className="w-12 h-12 text-purple-400" />
              </div>
            </div>
          </div>

          {/* Agent Cards Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {agents.map((agent) => (
              <div
                key={agent.name}
                className={`glass-effect rounded-2xl p-8 border ${agent.border} bg-gradient-to-br ${agent.gradient} backdrop-blur-xl hover:shadow-2xl transition-all duration-300 group`}
              >
                <div className="space-y-6">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-14 rounded-xl bg-white/10 flex items-center justify-center">
                        <agent.icon className={`w-8 h-8 ${agent.iconColor}`} />
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold">{agent.name}</h3>
                        <div className="flex items-center gap-2 mt-2">
                          <div className={`w-3 h-3 rounded-full bg-${agent.statusColor}-500 ${agent.status === "Processing" ? "animate-pulse" : ""}`} />
                          <span className="text-sm text-gray-400">{agent.status}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-gray-300 text-lg leading-relaxed">{agent.description}</p>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-white/5 rounded-xl p-4 backdrop-blur">
                      <p className="text-sm text-gray-400 mb-1">Tasks Completed</p>
                      <p className="text-2xl font-bold">{agent.tasks}</p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-4 backdrop-blur">
                      <p className="text-sm text-gray-400 mb-1">Avg Response</p>
                      <p className="text-2xl font-bold">{agent.avgResponse}</p>
                    </div>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-3">
                    {agent.tags.map((tag) => (
                      <span
                        key={tag}
                        className={`px-4 py-2 rounded-full text-xs font-medium border ${agent.border.replace("border-", "border-").replace("/30", "/30")} bg-${agent.gradient.split(" ")[1].split("/")[0]}/20 ${agent.iconColor.replace("text-", "text-")} backdrop-blur`}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}