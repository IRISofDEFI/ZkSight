"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Zap, Sparkles } from "lucide-react";
import { useState } from "react";
import { submitQuery } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useQueryStore } from "@/lib/store";
import { toast } from "sonner";

const exampleQueries = [
  "Show me transaction volume trends for the last 30 days",
  "What's the current network hashrate?",
  "Analyze block time distribution this week",
  "Compare shielded vs transparent transactions",
];

export default function QueryPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { addQuery } = useQueryStore();

  const handleAnalyze = async () => {
    if (!query.trim() || loading) return;

    setLoading(true);
    const text = query.trim();
    addQuery(text);

    toast.loading("Processing your query…", { id: "query" });

    try {
      const data = await submitQuery(text);
      toast.success("Analysis ready! Redirecting…", { id: "query" });

      router.push(`/report/${data.queryId}`);
    } catch (err: any) {
      toast.error(err.message || "Something went wrong", { id: "query" });
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-black text-white">
      <Sidebar />

      <div className="flex-1 flex flex-col">
        <Header />

        <main className="flex-1 overflow-y-auto px-12 py-10">
          {/* HEADER */}
          <div className="max-w-5xl mx-auto mb-12">
            <div className="flex items-center gap-5 mb-3">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 via-pink-500 to-cyan-500 flex items-center justify-center shadow-2xl">
                <Sparkles className="w-9 h-9 text-white" />
              </div>
              <div>
                <h1 className="text-5xl font-black tracking-tight">Natural Language Query</h1>
                <p className="text-gray-400 text-xl mt-1">
                  Ask anything about the Zcash network in plain English
                </p>
              </div>
            </div>
          </div>

          {/* MAIN QUERY BOX */}
          <div className="max-w-5xl mx-auto mb-20">
            <div className="relative">
              <Textarea
                placeholder="Ask anything about Zcash network data..."
                className="w-full min-h-56 bg-gray-900/40 border border-gray-800 rounded-3xl px-10 py-10 text-xl text-gray-300"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />

              <div className="absolute bottom-6 right-6">
                <Button
                  size="lg"
                  disabled={!query.trim() || loading}
                  onClick={handleAnalyze}
                  className="rounded-full bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-700 hover:to-cyan-700 text-white font-bold px-12 py-7 text-lg shadow-2xl flex items-center gap-3"
                >
                  {loading ? (
                    <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <Zap className="w-6 h-6" />
                  )}
                  ANALYZE
                </Button>
              </div>
            </div>
          </div>

          {/* EXAMPLE QUERIES */}
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center gap-4 mb-8">
              <Sparkles className="w-9 h-9 text-purple-400" />
              <h2 className="text-3xl font-bold tracking-tight">AI-POWERED QUERY EXAMPLES</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {exampleQueries.map((example, i) => (
                <button
                  key={i}
                  onClick={() => setQuery(example)}
                  className="group relative bg-gray-900/30 border border-gray-800 rounded-3xl p-8 text-left hover:bg-gray-900/50 hover:border-purple-500/60 transition-all"
                >
                  <div className="flex items-start gap-5">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600/30 to-cyan-600/30 flex items-center justify-center">
                      <Zap className="w-8 h-8 text-purple-400" />
                    </div>
                    <p className="text-lg text-gray-300 leading-relaxed pt-2">{example}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
