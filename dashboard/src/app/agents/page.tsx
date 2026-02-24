"use client";

import { useEffect, useState } from "react";
import { Bot, Play } from "lucide-react";
import AgentChat from "@/components/agent-chat";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8626";

interface AgentInfo {
  name: string;
  description: string;
  model: string;
  tools: string[];
  sessions?: number;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/agents/`)
      .then((r) => r.json())
      .then((data) => setAgents(data.agents || []))
      .catch(() => setError("Cannot connect to Forge server"));
  }, []);

  if (selectedAgent) {
    return (
      <div>
        <button
          onClick={() => setSelectedAgent(null)}
          className="text-sm text-gray-400 hover:text-gray-200 mb-4"
        >
          &larr; Back to agents
        </button>
        <AgentChat agentName={selectedAgent} />
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Agents</h2>

      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-lg p-4 mb-6 text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <div key={agent.name} className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-3">
              <Bot size={20} className="text-orange-400" />
              <h3 className="font-semibold text-lg">{agent.name}</h3>
            </div>
            {agent.description && (
              <p className="text-sm text-gray-400 mb-3">{agent.description}</p>
            )}
            <p className="text-xs text-gray-500 mb-3">{agent.model}</p>
            <div className="flex flex-wrap gap-1 mb-4">
              {agent.tools.map((tool) => (
                <span key={tool} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">
                  {tool}
                </span>
              ))}
            </div>
            <button
              onClick={() => setSelectedAgent(agent.name)}
              className="flex items-center gap-2 bg-orange-600 hover:bg-orange-500 text-white text-sm px-4 py-2 rounded-lg transition-colors"
            >
              <Play size={14} />
              Run Agent
            </button>
          </div>
        ))}
      </div>

      {agents.length === 0 && !error && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
          <Bot size={48} className="mx-auto mb-4 text-gray-700" />
          <p>No agents registered yet.</p>
          <p className="text-sm mt-2">
            Start the server with <code className="bg-gray-800 px-1 rounded">forge up</code>
          </p>
        </div>
      )}
    </div>
  );
}
