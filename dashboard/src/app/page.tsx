"use client";

import { useEffect, useState } from "react";
import { Bot, MessageSquare, DollarSign, Zap } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8626";
const WS_URL = API_URL.replace("http", "ws");

interface AgentInfo {
  name: string;
  description: string;
  model: string;
  tools: string[];
}

interface EventItem {
  type: string;
  agent_name: string;
  session_id: string;
  timestamp: string;
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ size?: number }>;
  color: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{label}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/agents/`)
      .then((r) => r.json())
      .then((data) => setAgents(data.agents || []))
      .catch(() => setError("Cannot connect to Forge server"));
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(`${WS_URL}/ws`);
      ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data);
          setEvents((prev) => [event, ...prev].slice(0, 50));
        } catch {}
      };
      ws.onerror = () => {};
    } catch {}
    return () => ws?.close();
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-lg p-4 mb-6 text-red-300 text-sm">
          {error} — Start the server with <code className="bg-gray-800 px-1 rounded">forge server</code>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Agents" value={agents.length} icon={Bot} color="bg-blue-900/50 text-blue-400" />
        <StatCard label="Sessions" value={0} icon={MessageSquare} color="bg-green-900/50 text-green-400" />
        <StatCard label="Total Cost" value="$0.00" icon={DollarSign} color="bg-yellow-900/50 text-yellow-400" />
        <StatCard label="Events" value={events.length} icon={Zap} color="bg-purple-900/50 text-purple-400" />
      </div>

      {/* Two columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agents */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Registered Agents</h3>
          {agents.length === 0 ? (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-gray-500 text-sm">
              No agents registered. Start with <code className="bg-gray-800 px-1 rounded">forge up</code>
            </div>
          ) : (
            <div className="space-y-3">
              {agents.map((agent) => (
                <div key={agent.name} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Bot size={16} className="text-orange-400" />
                    <span className="font-medium">{agent.name}</span>
                  </div>
                  <p className="text-xs text-gray-400 mb-2">{agent.model}</p>
                  <div className="flex flex-wrap gap-1">
                    {agent.tools.map((tool) => (
                      <span key={tool} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Events */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Live Event Feed</h3>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 max-h-96 overflow-y-auto">
            {events.length === 0 ? (
              <p className="text-gray-500 text-sm">Waiting for events...</p>
            ) : (
              <div className="space-y-2">
                {events.map((event, i) => {
                  const color = event.type.includes("error")
                    ? "text-red-400"
                    : event.type.includes("completed")
                    ? "text-green-400"
                    : "text-blue-400";
                  return (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <span className={`font-mono ${color}`}>{event.type}</span>
                      <span className="text-gray-500">{event.agent_name}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
