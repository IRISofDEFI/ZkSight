"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bell, Plus, Play, Trash2, Edit } from "lucide-react";
import { useState } from "react";

interface AlertRule {
  id: string;
  name: string;
  metric: string;
  operator: string;
  threshold: number;
  enabled: boolean;
  channels: string[];
}

interface AlertHistory {
  id: string;
  ruleId: string;
  ruleName: string;
  timestamp: number;
  message: string;
  severity: "info" | "warning" | "critical";
}

export default function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([
    {
      id: "1",
      name: "High Transaction Volume",
      metric: "tx_volume",
      operator: ">",
      threshold: 5000,
      enabled: true,
      channels: ["email", "webhook"],
    },
    {
      id: "2",
      name: "Low Hashrate",
      metric: "hashrate",
      operator: "<",
      threshold: 7000,
      enabled: false,
      channels: ["email"],
    },
  ]);

  const [history] = useState<AlertHistory[]>([
    {
      id: "h1",
      ruleId: "1",
      ruleName: "High Transaction Volume",
      timestamp: Date.now() - 3600000,
      message: "Transaction volume exceeded 5000 tx/hour",
      severity: "warning",
    },
    {
      id: "h2",
      ruleId: "1",
      ruleName: "High Transaction Volume",
      timestamp: Date.now() - 7200000,
      message: "Transaction volume exceeded 5000 tx/hour",
      severity: "warning",
    },
  ]);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newRule, setNewRule] = useState({
    name: "",
    metric: "tx_volume",
    operator: ">",
    threshold: 0,
  });

  const toggleRule = (id: string) => {
    setRules(rules.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r)));
  };

  const deleteRule = (id: string) => {
    setRules(rules.filter((r) => r.id !== id));
  };

  const createRule = () => {
    const rule: AlertRule = {
      id: Date.now().toString(),
      ...newRule,
      enabled: true,
      channels: ["email"],
    };
    setRules([...rules, rule]);
    setIsCreateOpen(false);
    setNewRule({ name: "", metric: "tx_volume", operator: ">", threshold: 0 });
  };

  const testRule = (rule: AlertRule) => {
    alert(`Testing rule: ${rule.name}\n\nThis would trigger a test alert to your configured channels.`);
  };

  const formatTime = (ts: number) => {
    const date = new Date(ts);
    const now = Date.now();
    const diff = now - ts;

    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto px-8 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
                <Bell className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-5xl font-black tracking-tight">Alert Management</h1>
                <p className="text-gray-400 text-xl mt-1">Configure rules and monitor alert history</p>
              </div>
            </div>

            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2 bg-green-600 hover:bg-green-700">
                  <Plus className="w-4 h-4" />
                  Create Alert Rule
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 text-white border-zinc-800">
                <DialogHeader>
                  <DialogTitle>Create Alert Rule</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <div>
                    <label className="text-sm text-zinc-400 mb-2 block">Rule Name</label>
                    <Input
                      value={newRule.name}
                      onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                      placeholder="e.g., High Transaction Volume"
                      className="bg-zinc-800 border-zinc-700"
                    />
                  </div>

                  <div>
                    <label className="text-sm text-zinc-400 mb-2 block">Metric</label>
                    <select
                      value={newRule.metric}
                      onChange={(e) => setNewRule({ ...newRule, metric: e.target.value })}
                      className="w-full p-3 rounded-lg bg-zinc-800 border border-zinc-700 focus:border-purple-500 outline-none"
                    >
                      <option value="tx_volume">Transaction Volume</option>
                      <option value="hashrate">Network Hashrate</option>
                      <option value="price">ZEC Price</option>
                      <option value="shielded_pool">Shielded Pool Size</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-zinc-400 mb-2 block">Operator</label>
                      <select
                        value={newRule.operator}
                        onChange={(e) => setNewRule({ ...newRule, operator: e.target.value })}
                        className="w-full p-3 rounded-lg bg-zinc-800 border border-zinc-700 focus:border-purple-500 outline-none"
                      >
                        <option value=">">Greater than (&gt;)</option>
                        <option value="<">Less than (&lt;)</option>
                        <option value="==">Equal to (==)</option>
                        <option value="change_pct">% Change</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-sm text-zinc-400 mb-2 block">Threshold</label>
                      <Input
                        type="number"
                        value={newRule.threshold}
                        onChange={(e) => setNewRule({ ...newRule, threshold: Number(e.target.value) })}
                        placeholder="0"
                        className="bg-zinc-800 border-zinc-700"
                      />
                    </div>
                  </div>

                  <Button onClick={createRule} className="w-full bg-purple-600 hover:bg-purple-700">
                    Create Rule
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="rules" className="w-full">
            <TabsList className="bg-zinc-900 border border-zinc-800">
              <TabsTrigger value="rules">Alert Rules ({rules.length})</TabsTrigger>
              <TabsTrigger value="history">Alert History ({history.length})</TabsTrigger>
            </TabsList>

            {/* Rules Tab */}
            <TabsContent value="rules" className="mt-6">
              <div className="space-y-4">
                {rules.map((rule) => (
                  <Card key={rule.id} className="p-6 bg-zinc-900/70 border-zinc-800">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-bold">{rule.name}</h3>
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-bold ${
                              rule.enabled
                                ? "bg-green-500/20 text-green-400 border border-green-500/40"
                                : "bg-zinc-700 text-zinc-400"
                            }`}
                          >
                            {rule.enabled ? "ENABLED" : "DISABLED"}
                          </span>
                        </div>
                        <p className="text-zinc-400 font-mono">
                          {rule.metric} {rule.operator} {rule.threshold}
                        </p>
                        <p className="text-sm text-zinc-500 mt-2">
                          Channels: {rule.channels.join(", ")}
                        </p>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => testRule(rule)}
                          title="Test Rule"
                        >
                          <Play className="w-4 h-4" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => toggleRule(rule.id)}
                          title={rule.enabled ? "Disable" : "Enable"}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => deleteRule(rule.id)}
                          className="text-red-400 hover:text-red-300"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}

                {rules.length === 0 && (
                  <div className="text-center py-20">
                    <Bell className="w-16 h-16 mx-auto mb-4 text-zinc-600" />
                    <h3 className="text-2xl font-bold mb-2">No alert rules yet</h3>
                    <p className="text-zinc-400 mb-6">Create your first alert rule to get started</p>
                    <Button onClick={() => setIsCreateOpen(true)} className="gap-2">
                      <Plus className="w-4 h-4" />
                      Create Alert Rule
                    </Button>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* History Tab */}
            <TabsContent value="history" className="mt-6">
              <div className="space-y-4">
                {history.map((alert) => (
                  <Card
                    key={alert.id}
                    className={`p-6 border-l-4 ${
                      alert.severity === "critical"
                        ? "border-l-red-500 bg-red-900/10"
                        : alert.severity === "warning"
                        ? "border-l-amber-500 bg-amber-900/10"
                        : "border-l-blue-500 bg-blue-900/10"
                    } bg-zinc-900/70 border-zinc-800`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-bold">{alert.ruleName}</h3>
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                              alert.severity === "critical"
                                ? "bg-red-500/20 text-red-400"
                                : alert.severity === "warning"
                                ? "bg-amber-500/20 text-amber-400"
                                : "bg-blue-500/20 text-blue-400"
                            }`}
                          >
                            {alert.severity}
                          </span>
                        </div>
                        <p className="text-zinc-300">{alert.message}</p>
                      </div>
                      <span className="text-sm text-zinc-500">{formatTime(alert.timestamp)}</span>
                    </div>
                  </Card>
                ))}

                {history.length === 0 && (
                  <div className="text-center py-20">
                    <Bell className="w-16 h-16 mx-auto mb-4 text-zinc-600" />
                    <h3 className="text-2xl font-bold mb-2">No alerts yet</h3>
                    <p className="text-zinc-400">Alert history will appear here when rules are triggered</p>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>

          {/* Info Box */}
          <div className="mt-8 p-6 bg-blue-900/20 border border-blue-500/30 rounded-xl">
            <h4 className="font-bold mb-2 text-blue-300">🚧 Alert Management - In Development</h4>
            <p className="text-sm text-zinc-400">
              This is a simplified version. Full features coming soon:
            </p>
            <ul className="text-sm text-zinc-400 mt-2 space-y-1 list-disc list-inside">
              <li>Real-time alert triggering from monitoring agent</li>
              <li>Multiple notification channels (Email, SMS, Webhook, Slack)</li>
              <li>Alert rule templates and presets</li>
              <li>Advanced condition builder (AND/OR logic)</li>
              <li>Alert acknowledgment and resolution tracking</li>
            </ul>
          </div>
        </main>
      </div>
    </div>
  );
}
