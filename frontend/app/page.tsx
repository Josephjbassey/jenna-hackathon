"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { ChatInterface } from "@/components/ChatInterface";
import { SegmentCanvas } from "@/components/SegmentCanvas";
import { MultimodalReasoningPanel } from "@/components/MultimodalReasoningPanel";
import { TaskQueueWidget } from "@/components/TaskQueueWidget";
import { MemoryModal } from "@/components/MemoryModal";
import {
  BoundingBox,
  SegmentCrop,
  SegmentResponse,
  SquadRoleInfo,
  getHealth,
  getSquadRoles,
} from "@/lib/api";

export default function Home() {
  const [activeRole, setActiveRole] = useState<string>("commander");
  const [activeView, setActiveView] = useState<"dashboard" | "queue" | "memory">(
    "dashboard"
  );
  const [backendConnected, setBackendConnected] = useState<boolean>(true);
  const [roles, setRoles] = useState<SquadRoleInfo[]>([
    {
      role: "commander",
      name: "Jenna Commander",
      model: "muse-spark-1.3",
      description: "Executive coordinator, voice conversationalist, and task decomposer.",
      capabilities: ["Orchestration", "Task Delegation", "Dialogue Flow"],
    },
    {
      role: "planner",
      name: "Jenna Planner",
      model: "muse-spark-1.3",
      description: "Multi-step reasoning, structured task planning, agent orchestration.",
      capabilities: ["Hierarchical Planning", "Dependency Mapping", "Verification"],
    },
    {
      role: "coder",
      name: "Jenna Engineer",
      model: "muse-code",
      description: "Code generation, debugging, refactoring, terminal tasks.",
      capabilities: ["Full-Stack Dev", "Bug Fixing", "AST Validation"],
    },
    {
      role: "researcher",
      name: "Jenna Scholar",
      model: "muse-spark-1.3",
      description: "Web research, factual aggregation, documentation, vision analysis.",
      capabilities: ["Deep Research", "Multimodal Grounding", "Synthesis"],
    },
    {
      role: "desktop",
      name: "Jenna Operator",
      model: "sam-3.1",
      description: "Desktop automation, GUI inspection, click-and-type execution.",
      capabilities: ["SAM 3.1 Segmentation", "Screen Inspection", "Window Tracking"],
    },
  ]);

  // Selected segment for multimodal reasoning pipeline
  const [selectedCrop, setSelectedCrop] = useState<SegmentCrop | null>(null);
  const [selectedBox, setSelectedBox] = useState<BoundingBox | null>(null);

  // Poll backend health and roles on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const health = await getHealth();
        setBackendConnected(health.status === "healthy" || health.status === "ok");
      } catch (err) {
        setBackendConnected(false);
      }
    };

    const fetchRoles = async () => {
      try {
        const res = await getSquadRoles();
        if (res.roles && res.roles.length > 0) {
          setRoles(res.roles);
        }
      } catch (err) {
        // Fallback to default squad roles if backend is not yet started
      }
    };

    checkConnection();
    fetchRoles();
    const interval = setInterval(checkConnection, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectSegment = (crop: SegmentCrop, box: BoundingBox) => {
    setSelectedCrop(crop);
    setSelectedBox(box);
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#0b0f17]">
      <Navbar
        activeRole={activeRole}
        onSelectRole={setActiveRole}
        roles={roles}
        backendConnected={backendConnected}
        activeView={activeView}
        setActiveView={setActiveView}
        onOpenMemory={() => setActiveView("memory")}
        onOpenQueue={() => setActiveView("queue")}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 flex flex-col">
        {activeView === "dashboard" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 min-h-[780px]">
            {/* Left Column: Real-Time Agentic Dialogue (5 Cols) */}
            <div className="lg:col-span-5 h-[780px]">
              <ChatInterface
                activeRole={activeRole}
                onSelectRole={setActiveRole}
                roles={roles}
              />
            </div>

            {/* Right Column: SAM 3.1 Segmentation & Muse Spark Reasoning (7 Cols) */}
            <div className="lg:col-span-7 flex flex-col space-y-5 h-[780px]">
              <div className="h-[430px]">
                <SegmentCanvas
                  onSelectSegmentForReasoning={handleSelectSegment}
                />
              </div>
              <div className="flex-1 min-h-[320px]">
                <MultimodalReasoningPanel
                  selectedCrop={selectedCrop}
                  selectedBox={selectedBox}
                />
              </div>
            </div>
          </div>
        )}

        {activeView === "queue" && (
          <div className="flex-1 min-h-[700px]">
            <TaskQueueWidget />
          </div>
        )}

        {activeView === "memory" && (
          <div className="flex-1 min-h-[700px]">
            <MemoryModal />
          </div>
        )}
      </main>
    </div>
  );
}
