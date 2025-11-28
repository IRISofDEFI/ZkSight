"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Button } from "@/components/ui/button";
import { Loader2, FileText, Sparkles, Download, ArrowRight } from "lucide-react";
import { toast } from "sonner";

export default function ReportPage() {
  const { id } = useParams();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<any>(null);
  const [error, setError] = useState("");

  // Mock follow-up questions
  const [followUpQuestions] = useState([
    "What caused this trend?",
    "Compare this to last month",
    "Show me related metrics",
    "Predict next week's values",
  ]);

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

  const exportReport = (format: "pdf" | "html" | "json") => {
    // TODO: Implement actual export
    toast.success(`Exporting report as ${format.toUpperCase()}...`, {
      description: "This feature is coming soon!",
    });
  };

  const askFollowUp = (question: string) => {
    router.push(`/query?q=${encodeURIComponent(question)}`);
  };

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto px-10 py-10">
          {/* PAGE TITLE */}
          <div className="flex items-center justify-between mb-10">
            <div className="flex items-center gap-4">
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

            {/* Export Buttons */}
            {!loading && report && (
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => exportReport("pdf")}
                  className="gap-2"
                >
                  <Download className="w-4 h-4" />
                  PDF
                </Button>
                <Button
                  variant="outline"
                  onClick={() => exportReport("html")}
                  className="gap-2"
                >
                  <Download className="w-4 h-4" />
                  HTML
                </Button>
                <Button
                  variant="outline"
                  onClick={() => exportReport("json")}
                  className="gap-2"
                >
                  <Download className="w-4 h-4" />
                  JSON
                </Button>
              </div>
            )}
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

              {/* FOLLOW-UP QUESTIONS */}
              <div className="glass-card rounded-3xl p-10 border border-green-500/20">
                <div className="flex items-center gap-3 mb-6">
                  <Sparkles className="w-8 h-8 text-green-400" />
                  <h2 className="text-3xl font-black text-green-300">
                    Follow-up Questions
                  </h2>
                </div>

                <p className="text-zinc-400 mb-6">
                  Explore deeper insights with these AI-suggested questions:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {followUpQuestions.map((question, i) => (
                    <button
                      key={i}
                      onClick={() => askFollowUp(question)}
                      className="group p-6 rounded-2xl bg-zinc-800/50 border border-zinc-700 hover:border-green-500/50 transition-all text-left"
                    >
                      <div className="flex items-center justify-between">
                        <p className="text-zinc-300 font-medium">{question}</p>
                        <ArrowRight className="w-5 h-5 text-green-400 group-hover:translate-x-1 transition-transform" />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
