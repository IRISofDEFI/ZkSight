"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Loader2, FileText, Sparkles } from "lucide-react";

export default function ReportPage() {
  const { id } = useParams();

  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadReport() {
      try {
        const res = await fetch(`/api/reports/${id}`);
        if (!res.ok) {
          throw new Error("Report not found");
        }
        const data = await res.json();
        setReport(data);
      } catch (err: any) {
        setError(err.message || "Failed to load report");
      } finally {
        setLoading(false);
      }
    }

    loadReport();
  }, [id]);

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto px-10 py-10">
          {/* PAGE TITLE */}
          <div className="flex items-center gap-4 mb-10">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-[0_0_30px_rgba(147,51,234,0.6)]">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-5xl font-black tracking-tight">
                Report Details
              </h1>
              <p className="text-gray-400 text-lg mt-1 font-mono">
                Query ID: <span className="text-purple-300">{id}</span>
              </p>
            </div>
          </div>

          {/* LOADING STATE */}
          {loading && (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="animate-spin w-10 h-10 text-purple-400" />
            </div>
          )}

          {/* ERROR STATE */}
          {!loading && error && (
            <div className="text-center text-red-400 font-bold text-lg">
              {error}
            </div>
          )}

          {/* REPORT VIEW */}
          {!loading && report && (
            <div className="space-y-10">
              {/* SUMMARY CARD */}
              <div className="glass-card rounded-3xl p-10 border border-purple-500/20 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-pink-500/5 opacity-50" />

                <div className="relative">
                  <h2 className="text-3xl font-black mb-3 text-purple-300">
                    Summary
                  </h2>
                  <p className="text-gray-300 leading-relaxed text-lg whitespace-pre-line">
                    {report.summary}
                  </p>
                </div>
              </div>

              {/* INSIGHTS */}
              {report.insights?.length > 0 && (
                <div className="glass-card rounded-3xl p-10 border border-amber-500/20">
                  <h2 className="text-3xl font-black text-amber-300 mb-6">
                    Key Insights
                  </h2>

                  <div className="space-y-6">
                    {report.insights.map((insight: string, i: number) => (
                      <div
                        key={i}
                        className="glass-card p-6 rounded-2xl border border-white/10 hover:border-amber-500/30 transition-all relative group"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-amber-500/0 to-amber-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="relative flex gap-4 items-start">
                          <Sparkles className="w-6 h-6 text-amber-400 mt-1" />
                          <p className="text-gray-300 font-mono">{insight}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* RAW DATA / TECHNICAL */}
              {report.data && (
                <div className="glass-card rounded-3xl p-10 border border-blue-500/20">
                  <h2 className="text-3xl font-black text-blue-300 mb-6">
                    Technical Data
                  </h2>

                  <pre className="bg-black/40 p-6 rounded-2xl text-sm text-gray-300 overflow-x-auto border border-blue-500/20">
                    {JSON.stringify(report.data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
