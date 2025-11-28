// src/components/query-bar.tsx
"use client";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";
import { useState } from "react";
import { submitQuery } from "@/lib/api";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { useQueryStore } from "@/lib/store";

export function QueryBar() {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { addQuery } = useQueryStore();

  const handleSubmit = async () => {
    if (!query.trim() || isLoading) return;

    const queryText = query.trim();
    setIsLoading(true);
    addQuery(queryText); // ← saves to history instantly
    toast.loading("Chimera is thinking...", { id: "query" });

    try {
      const data = await submitQuery(queryText);
      toast.success("Query received! Redirecting...", { id: "query" });
      setQuery(""); // clear input
      router.push(`/report/${data.queryId}`);
    } catch (err: any) {
      toast.error(err.message || "Something went wrong", { id: "query" });
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="relative">
        <Textarea
          placeholder="Ask anything about Zcash... e.g. Show shielded pool growth last 6 months"
          className="min-h-32 text-lg resize-none pr-16 bg-card border-2 focus:border-primary"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          disabled={isLoading}
        />
        <Button
          size="icon"
          className="absolute bottom-4 right-4 rounded-full"
          onClick={handleSubmit}
          disabled={!query.trim() || isLoading}
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-t-transparent border-white rounded-full animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </Button>
      </div>
      <p className="text-sm text-muted-foreground mt-3 text-center">
        Press Enter to send • We use AI agents to analyze on-chain, market, and social data
      </p>
    </div>
  );
}