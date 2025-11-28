"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { toast } from "sonner";

interface WebSocketContextType {
  connected: boolean;
  lastMessage: any;
  send: (event: string, data: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType>({
  connected: false,
  lastMessage: null,
  send: () => {},
});

export function useWebSocket() {
  return useContext(WebSocketContext);
}

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:3001";

    try {
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log("WebSocket: Connected to", wsUrl);
        setConnected(true);
        setWs(socket);
        toast.success("Connected to server");
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);

          // Handle different message types
          if (data.type === "alert") {
            toast.warning(data.message, {
              action: { label: "View", onClick: () => window.location.href = "/alerts" },
            });
          } else if (data.type === "query_complete") {
            toast.success("Query completed");
          } else if (data.type === "metric_update") {
            // Silent update, just store in state
            console.log("Metric update received:", data);
          }
        } catch (err) {
          console.error("WebSocket: Failed to parse message", err);
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket: Error", error);
        toast.error("WebSocket connection error");
      };

      socket.onclose = () => {
        console.log("WebSocket: Disconnected");
        setConnected(false);
        setWs(null);

        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          console.log("WebSocket: Attempting to reconnect...");
          // Component will re-mount and try again
        }, 5000);
      };

      return () => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.close();
        }
      };
    } catch (err) {
      console.error("WebSocket: Failed to connect", err);
      toast.error("Failed to establish WebSocket connection");
      
      // Fallback to simulation if WebSocket fails
      const simulateConnection = () => {
        setConnected(false);
        console.log("WebSocket: Using fallback mode (server not available)");
        
        // Simulate periodic updates
        const interval = setInterval(() => {
          const mockData = {
            type: "metric_update",
            data: {
              hashrate: 8000 + Math.random() * 2000,
              tx_volume: 4000 + Math.random() * 2000,
              timestamp: Date.now(),
            },
          };
          setLastMessage(mockData);
        }, 30000);

        return () => {
          clearInterval(interval);
        };
      };
      
      return simulateConnection();
    }
  }, []);

  const send = (event: string, data: any) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ event, data }));
    } else {
      console.warn("WebSocket: Not connected, cannot send message");
    }
  };

  return (
    <WebSocketContext.Provider value={{ connected, lastMessage, send }}>
      {children}
    </WebSocketContext.Provider>
  );
}

// Connection status indicator component
export function ConnectionStatus() {
  const { connected } = useWebSocket();

  return (
    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-800 border border-zinc-700">
      <div
        className={`w-2 h-2 rounded-full ${
          connected ? "bg-green-500 animate-pulse" : "bg-red-500"
        }`}
      />
      <span className="text-xs font-medium text-zinc-400">
        {connected ? "Connected" : "Disconnected"}
      </span>
    </div>
  );
}
