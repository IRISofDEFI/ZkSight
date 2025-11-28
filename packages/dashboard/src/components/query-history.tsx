// src/components/query-history.tsx
"use client";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Clock, Trash2, Sparkles } from "lucide-react";
import { useQueryStore, QueryItem } from "@/lib/store";
import { useRouter } from "next/navigation";

export function QueryHistory() {
  const { history, clearHistory } = useQueryStore();
  const router = useRouter();

  const formatTime = (ts: number) => {
    const date = new Date(ts);
    const now = Date.now();
    const diff = now - ts;

    if (diff < 60_000) return "just now";
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
    return date.toLocaleDateString();
  };

  if (history.length === 0) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        <Sparkles className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>No queries yet</p>
        <p className="text-sm">Your history will appear here</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-semibold flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Recent Queries
        </h3>
        <Button
          variant="ghost"
          size="icon"
          onClick={clearHistory}
          className="h-8 w-8"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {history.map((item) => (
            <button
              key={item.id}
              onClick={() => router.push(`/report/${item.id.replace("q-", "demo-")}`)}
              className="w-full text-left p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors group"
            >
              <p className="text-sm font-medium line-clamp-2">{item.text}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {formatTime(item.timestamp)}
              </p>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}