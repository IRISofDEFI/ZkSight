// src/components/alert-provider.tsx
"use client";

import { useEffect } from "react";
import { toast } from "sonner";

const messages = [
  "Shielded pool just crossed 4.20M ZEC!",
  "Unusual spike in shielded transactions detected",
  "ZEC price up +7.3% in the last hour",
  "Sentiment score jumped from 72 → 89",
  "Over 3,000 tx/min — highest since March",
];

export function AlertProvider() {
  useEffect(() => {
    let i = 0;
    const show = () => {
      toast.success(messages[i % messages.length], {
        duration: 7000,
        action: { label: "View", onClick: () => window.location.href = "/dashboard" },
      });
      i++;
    };
    show(); // first one immediately
    const id = setInterval(show, 30000 + Math.random() * 30000);
    return () => clearInterval(id);
  }, []);
  return null;
}