"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  Bot,
  User,
  Terminal,
  Code,
  Compass,
  Monitor,
  Zap,
  StopCircle,
} from "lucide-react";
import { ChatMessage, streamAgentChat, SquadRoleInfo } from "@/lib/api";

interface ChatInterfaceProps {
  activeRole: string;
  onSelectRole: (role: string) => void;
  roles: SquadRoleInfo[];
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  activeRole,
  onSelectRole,
  roles,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hello! I am Jenna, your autonomous AI assistant. I've been refactored into a decoupled Next.js + FastAPI architecture with direct access to Meta Model API (SAM 3.1, Muse Spark 1.3, and Muse Code). How can I assist you today?",
      agent_role: "commander",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingDelta, setStreamingDelta] = useState("");
  const abortRef = useRef<(() => void) | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingDelta]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isStreaming) return;

    const userMessage: ChatMessage = { role: "user", content: text };
    const newHistory = [...messages, userMessage];

    setMessages(newHistory);
    setInputValue("");
    setIsStreaming(true);
    setStreamingDelta("");

    let currentResponse = "";

    const stopFn = await streamAgentChat({
      messages: newHistory,
      agentRole: activeRole,
      onToken: (token) => {
        currentResponse += token;
        setStreamingDelta(currentResponse);
      },
      onFinish: (role) => {
        setIsStreaming(false);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: currentResponse,
            agent_role: role,
          },
        ]);
        setStreamingDelta("");
        abortRef.current = null;
      },
      onError: (err) => {
        console.error("Chat streaming error:", err);
        setIsStreaming(false);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `[System Error]: ${err.message}`,
            agent_role: "commander",
          },
        ]);
        setStreamingDelta("");
        abortRef.current = null;
      },
    });

    abortRef.current = stopFn;
  };

  const handleStopStream = () => {
    if (abortRef.current) {
      abortRef.current();
      setIsStreaming(false);
      if (streamingDelta) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: streamingDelta + " [Stream Interrupted]",
            agent_role: activeRole,
          },
        ]);
      }
      setStreamingDelta("");
    }
  };

  const getRoleIcon = (role?: string) => {
    switch (role) {
      case "planner":
        return <Compass className="w-3.5 h-3.5 text-amber-400" />;
      case "coder":
        return <Code className="w-3.5 h-3.5 text-cyan-400" />;
      case "researcher":
        return <Sparkles className="w-3.5 h-3.5 text-purple-400" />;
      case "desktop":
        return <Monitor className="w-3.5 h-3.5 text-emerald-400" />;
      default:
        return <Bot className="w-3.5 h-3.5 text-cyan-400" />;
    }
  };

  const quickPrompts = [
    "Run SAM 3.1 visual segmentation on the active workspace frame.",
    "Formulate a structured execution plan for agent orchestration.",
    "Generate async FastAPI endpoints with Pydantic v2 schemas.",
    "Inspect cross-agent memory for recent developer sessions.",
  ];

  return (
    <div className="flex flex-col h-full bg-[#111726]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <h2 className="font-semibold text-sm text-slate-100">
            Real-Time Agentic Dialogue
          </h2>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-300">
            Active: {activeRole.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto space-y-3.5 my-3 pr-1">
        {messages.map((msg, idx) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={idx}
              className={`flex items-start space-x-2.5 ${
                isUser ? "flex-row-reverse space-x-reverse" : ""
              }`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  isUser
                    ? "bg-cyan-500 text-black font-bold text-xs"
                    : "bg-slate-800 border border-slate-700 text-cyan-400"
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : getRoleIcon(msg.agent_role)}
              </div>

              <div
                className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-xs leading-relaxed ${
                  isUser
                    ? "bg-cyan-600 text-slate-50 shadow-md shadow-cyan-600/10"
                    : "bg-slate-900/90 border border-slate-800 text-slate-200"
                }`}
              >
                {!isUser && msg.agent_role && (
                  <div className="text-[10px] font-mono text-cyan-400 mb-1 flex items-center space-x-1">
                    <span>JENNA {msg.agent_role.toUpperCase()}</span>
                  </div>
                )}
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          );
        })}

        {/* Live Streaming Delta Bubble */}
        {isStreaming && (
          <div className="flex items-start space-x-2.5">
            <div className="w-7 h-7 rounded-lg bg-slate-800 border border-cyan-500/40 text-cyan-400 flex items-center justify-center flex-shrink-0">
              {getRoleIcon(activeRole)}
            </div>
            <div className="max-w-[85%] rounded-xl px-3.5 py-2.5 text-xs bg-slate-900/90 border border-cyan-500/30 text-slate-200">
              <div className="text-[10px] font-mono text-cyan-400 mb-1 flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                <span>STREAMING FROM {activeRole.toUpperCase()}</span>
              </div>
              <div className="whitespace-pre-wrap">
                {streamingDelta}
                <span className="animate-cursor" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Chips */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-2 text-[11px]">
        {quickPrompts.map((qp, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(qp)}
            disabled={isStreaming}
            className="flex-shrink-0 px-2.5 py-1 rounded-md bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
          >
            {qp}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="relative pt-2 border-t border-slate-800">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder={`Instruct Jenna ${activeRole} (Shift+Enter for newline)...`}
          rows={2}
          className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3 py-2 pr-20 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 resize-none"
        />

        <div className="absolute right-2 bottom-3 flex items-center space-x-1.5">
          {isStreaming ? (
            <button
              onClick={handleStopStream}
              className="p-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white transition-colors"
              title="Stop streaming"
            >
              <StopCircle className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => handleSend()}
              disabled={!inputValue.trim()}
              className="p-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-cyan-500/20"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
