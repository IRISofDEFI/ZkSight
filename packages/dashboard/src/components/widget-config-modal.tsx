"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState } from "react";

interface Widget {
  i: string;
  type: string;
  title: string;
  config: any;
}

interface WidgetConfigModalProps {
  widget: Widget;
  onSave: (config: any) => void;
  onClose: () => void;
}

const METRICS = [
  { value: "hashrate", label: "Network Hashrate" },
  { value: "tx_volume", label: "Transaction Volume" },
  { value: "price", label: "ZEC Price" },
  { value: "shielded_pool", label: "Shielded Pool Size" },
  { value: "block_time", label: "Block Time" },
  { value: "difficulty", label: "Network Difficulty" },
];

const TIME_RANGES = [
  { value: "1h", label: "Last Hour" },
  { value: "24h", label: "Last 24 Hours" },
  { value: "7d", label: "Last 7 Days" },
  { value: "30d", label: "Last 30 Days" },
  { value: "90d", label: "Last 90 Days" },
];

const CHART_TYPES = [
  { value: "line", label: "Line Chart" },
  { value: "area", label: "Area Chart" },
  { value: "bar", label: "Bar Chart" },
  { value: "candlestick", label: "Candlestick" },
];

export function WidgetConfigModal({ widget, onSave, onClose }: WidgetConfigModalProps) {
  const [title, setTitle] = useState(widget.title);
  const [metric, setMetric] = useState(widget.config.metric || "hashrate");
  const [timeRange, setTimeRange] = useState(widget.config.timeRange || "24h");
  const [chartType, setChartType] = useState(widget.config.chartType || "line");
  const [refreshInterval, setRefreshInterval] = useState(widget.config.refreshInterval || "30");

  const handleSave = () => {
    onSave({
      title,
      config: {
        metric,
        timeRange,
        chartType,
        refreshInterval: parseInt(refreshInterval),
      },
    });
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="bg-zinc-900 text-white border-zinc-800 max-w-md">
        <DialogHeader>
          <DialogTitle>Configure {widget.type} Widget</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Title */}
          <div>
            <Label className="text-sm text-zinc-400 mb-2 block">Widget Title</Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Network Hashrate"
              className="bg-zinc-800 border-zinc-700"
            />
          </div>

          {/* Metric Selection */}
          <div>
            <Label className="text-sm text-zinc-400 mb-2 block">Metric</Label>
            <Select value={metric} onValueChange={setMetric}>
              <SelectTrigger className="bg-zinc-800 border-zinc-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-zinc-800 border-zinc-700">
                {METRICS.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Time Range */}
          <div>
            <Label className="text-sm text-zinc-400 mb-2 block">Time Range</Label>
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="bg-zinc-800 border-zinc-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-zinc-800 border-zinc-700">
                {TIME_RANGES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Chart Type (for chart widgets) */}
          {(widget.type === "line-chart" || widget.type === "bar-chart") && (
            <div>
              <Label className="text-sm text-zinc-400 mb-2 block">Chart Type</Label>
              <Select value={chartType} onValueChange={setChartType}>
                <SelectTrigger className="bg-zinc-800 border-zinc-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-800 border-zinc-700">
                  {CHART_TYPES.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Refresh Interval */}
          <div>
            <Label className="text-sm text-zinc-400 mb-2 block">
              Refresh Interval (seconds)
            </Label>
            <Input
              type="number"
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(e.target.value)}
              min="5"
              max="300"
              className="bg-zinc-800 border-zinc-700"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              onClick={onClose}
              variant="outline"
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              className="flex-1 bg-purple-600 hover:bg-purple-700"
            >
              Save Configuration
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
