"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Wrench, ChevronDown, ChevronRight } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8626";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  cost?: number;
  steps?: number;
  toolCalls?: { tool: string; output: string }[];
}

export default function AgentChat({ agentName }: { agentName: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState<Set<number>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const createSession = async () => {
    const res = await fetch(`${API_URL}/api/v1/sessions/${agentName}/new`, {
      method: "POST",
    });
    const data = await res.json();
    return data.session_id;
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      let sid = sessionId;
      if (!sid) {
        sid = await createSession();
        setSessionId(sid);
      }

      const res = await fetch(
        `${API_URL}/api/v1/sessions/${agentName}/${sid}/message`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: userMsg }),
        }
      );
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response || data.error || "No response",
          cost: data.cost,
          steps: data.steps,
        },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: Could not reach the server." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleTool = (idx: number) => {
    setExpandedTools((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl flex flex-col h-[600px]">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <h3 className="font-semibold">{agentName}</h3>
        {sessionId && (
          <p className="text-xs text-gray-500 mt-1">Session: {sessionId.slice(0, 8)}...</p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${
                msg.role === "user"
                  ? "bg-orange-600 text-white"
                  : "bg-gray-800 text-gray-200"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.toolCalls.map((tc, j) => (
                    <div key={j} className="bg-gray-700/50 rounded p-2">
                      <button
                        onClick={() => toggleTool(i * 100 + j)}
                        className="flex items-center gap-1 text-xs text-cyan-400"
                      >
                        {expandedTools.has(i * 100 + j) ? (
                          <ChevronDown size={12} />
                        ) : (
                          <ChevronRight size={12} />
                        )}
                        <Wrench size={12} />
                        {tc.tool}
                      </button>
                      {expandedTools.has(i * 100 + j) && (
                        <pre className="text-xs text-gray-400 mt-1 overflow-x-auto">
                          {tc.output}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {msg.role === "assistant" && msg.cost !== undefined && (
                <p className="text-xs text-gray-500 mt-2">
                  Cost: ${msg.cost.toFixed(4)} | Steps: {msg.steps || 0}
                </p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg px-4 py-3 text-sm text-gray-400">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Type a message..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-orange-500"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
