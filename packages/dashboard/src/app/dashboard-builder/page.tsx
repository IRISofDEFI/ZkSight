"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Plus, Settings, Share2, Save, LayoutGrid, X } from "lucide-react";
import { useState } from "react";
import GridLayout from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import { WidgetConfigModal } from "@/components/widget-config-modal";

const WIDGET_TYPES = [
  { id: "metric", name: "Metric Card", icon: "📊" },
  { id: "line-chart", name: "Line Chart", icon: "📈" },
  { id: "bar-chart", name: "Bar Chart", icon: "📊" },
  { id: "pie-chart", name: "Pie Chart", icon: "🥧" },
  { id: "table", name: "Data Table", icon: "📋" },
  { id: "alert-list", name: "Alert List", icon: "🔔" },
];

interface Widget {
  i: string;
  x: number;
  y: number;
  w: number;
  h: number;
  type: string;
  title: string;
  config: any;
}

export default function DashboardBuilderPage() {
  const [widgets, setWidgets] = useState<Widget[]>([
    { i: "w1", x: 0, y: 0, w: 3, h: 2, type: "metric", title: "Network Hashrate", config: { metric: "hashrate" } },
    { i: "w2", x: 3, y: 0, w: 6, h: 4, type: "line-chart", title: "Transaction Volume", config: { metric: "tx_volume" } },
  ]);

  const [dashboardName, setDashboardName] = useState("My Dashboard");
  const [isAddWidgetOpen, setIsAddWidgetOpen] = useState(false);
  const [configWidget, setConfigWidget] = useState<Widget | null>(null);

  const addWidget = (type: string) => {
    const newWidget: Widget = {
      i: `w${Date.now()}`,
      x: 0,
      y: Infinity, // Puts it at the bottom
      w: 3,
      h: 2,
      type,
      title: `New ${type}`,
      config: {},
    };
    setWidgets([...widgets, newWidget]);
    setIsAddWidgetOpen(false);
  };

  const removeWidget = (id: string) => {
    setWidgets(widgets.filter((w) => w.i !== id));
  };

  const onLayoutChange = (layout: any[]) => {
    const updatedWidgets = widgets.map((widget) => {
      const layoutItem = layout.find((l) => l.i === widget.i);
      if (layoutItem) {
        return { ...widget, x: layoutItem.x, y: layoutItem.y, w: layoutItem.w, h: layoutItem.h };
      }
      return widget;
    });
    setWidgets(updatedWidgets);
  };

  const saveDashboard = async () => {
    // TODO: Save to API
    console.log("Saving dashboard:", { name: dashboardName, widgets });
    alert("Dashboard saved! (This will save to database when backend is connected)");
  };

  const shareDashboard = () => {
    alert("Share functionality coming soon!");
  };

  const updateWidgetConfig = (widgetId: string, config: any) => {
    setWidgets(widgets.map(w => w.i === widgetId ? { ...w, ...config } : w));
    setConfigWidget(null);
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
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <LayoutGrid className="w-8 h-8 text-white" />
              </div>
              <div>
                <Input
                  value={dashboardName}
                  onChange={(e) => setDashboardName(e.target.value)}
                  className="text-3xl font-black bg-transparent border-none focus:outline-none focus:ring-0 p-0 h-auto text-white"
                />
                <p className="text-gray-400 text-lg">Drag and resize widgets to customize</p>
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={shareDashboard} variant="outline" className="gap-2">
                <Share2 className="w-4 h-4" />
                Share
              </Button>
              <Button onClick={saveDashboard} className="gap-2 bg-purple-600 hover:bg-purple-700">
                <Save className="w-4 h-4" />
                Save Dashboard
              </Button>
            </div>
          </div>

          {/* Toolbar */}
          <div className="mb-6 flex gap-3">
            <Dialog open={isAddWidgetOpen} onOpenChange={setIsAddWidgetOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2 bg-green-600 hover:bg-green-700">
                  <Plus className="w-4 h-4" />
                  Add Widget
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 text-white border-zinc-800">
                <DialogHeader>
                  <DialogTitle>Add Widget</DialogTitle>
                </DialogHeader>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  {WIDGET_TYPES.map((type) => (
                    <button
                      key={type.id}
                      onClick={() => addWidget(type.id)}
                      className="p-6 rounded-xl bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-purple-500 transition-all text-center"
                    >
                      <div className="text-4xl mb-2">{type.icon}</div>
                      <div className="font-semibold">{type.name}</div>
                    </button>
                  ))}
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Dashboard Grid */}
          <div className="bg-zinc-900/30 rounded-3xl p-6 border border-zinc-800">
            {widgets.length === 0 ? (
              <div className="text-center py-20">
                <LayoutGrid className="w-16 h-16 mx-auto mb-4 text-zinc-600" />
                <h3 className="text-2xl font-bold mb-2">No widgets yet</h3>
                <p className="text-zinc-400 mb-6">Add your first widget to get started</p>
                <Button onClick={() => setIsAddWidgetOpen(true)} className="gap-2">
                  <Plus className="w-4 h-4" />
                  Add Widget
                </Button>
              </div>
            ) : (
              <GridLayout
                className="layout"
                layout={widgets}
                cols={12}
                rowHeight={60}
                width={1200}
                onLayoutChange={onLayoutChange}
                draggableHandle=".drag-handle"
              >
                {widgets.map((widget) => (
                  <div key={widget.i} className="bg-zinc-800 rounded-xl border border-zinc-700 overflow-hidden">
                    <div className="drag-handle cursor-move bg-zinc-900 px-4 py-3 flex items-center justify-between border-b border-zinc-700">
                      <h3 className="font-bold">{widget.title}</h3>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setConfigWidget(widget)}
                          className="p-1 hover:bg-zinc-700 rounded"
                        >
                          <Settings className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => removeWidget(widget.i)}
                          className="p-1 hover:bg-red-900/50 rounded text-red-400"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div className="p-4 h-full flex items-center justify-center text-zinc-500">
                      {widget.type} widget
                      <br />
                      (visualization here)
                    </div>
                  </div>
                ))}
              </GridLayout>
            )}
          </div>

          {/* Info */}
          <div className="mt-6 p-4 bg-green-900/20 border border-green-500/30 rounded-xl">
            <h4 className="font-bold mb-2 text-green-300">✅ Drag-and-Drop Enabled!</h4>
            <p className="text-sm text-zinc-400">
              Drag widgets by their header to reposition. Resize by dragging the bottom-right corner.
            </p>
          </div>
        </main>
      </div>

      {/* Widget Config Modal */}
      {configWidget && (
        <WidgetConfigModal
          widget={configWidget}
          onSave={(config) => updateWidgetConfig(configWidget.i, config)}
          onClose={() => setConfigWidget(null)}
        />
      )}
    </div>
  );
}
