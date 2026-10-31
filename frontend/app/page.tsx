"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { SegmentCanvas } from "@/components/SegmentCanvas";
import { MultimodalReasoningPanel } from "@/components/MultimodalReasoningPanel";
import { StorefrontPreview } from "@/components/StorefrontPreview";
import { TaskQueueWidget } from "@/components/TaskQueueWidget";
import { ChatInterface } from "@/components/ChatInterface";
import {
  BoundingBox,
  MerchantContext,
  StorefrontSchema,
  StructuredReasoningOutput,
  CodeGenerateResponse,
  PipelineResponse,
  SquadRoleInfo,
  getHealth,
  getSquadRoles,
  generateStorefrontCode,
} from "@/lib/api";
import {
  Bot,
  MessageSquare,
  Sparkles,
  Store,
  Layers,
  Code2,
  X,
  ChevronRight,
} from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"pipeline" | "storefront" | "queue">("pipeline");
  const [backendConnected, setBackendConnected] = useState<boolean>(true);
  const [chatOpen, setChatOpen] = useState<boolean>(false);
  const [activeRole, setActiveRole] = useState<string>("commander");
  const [isGeneratingCode, setIsGeneratingCode] = useState<boolean>(false);

  // Merchant context for localized reasoning
  const [merchantContext, setMerchantContext] = useState<MerchantContext>({
    store_name: "Mama Cass Market",
    currency: "NGN",
    location: "Akure Central Market, Ondo State, Nigeria",
    whatsapp_number: "+2348012345678",
  });

  // State populated through 3-model pipeline
  const [selectedBox, setSelectedBox] = useState<BoundingBox | null>(null);
  const [storeSchema, setStoreSchema] = useState<StorefrontSchema | null>(null);
  const [structuredOutput, setStructuredOutput] = useState<StructuredReasoningOutput | null>(null);
  const [codeResponse, setCodeResponse] = useState<CodeGenerateResponse | null>(null);

  // Available agent roles for conversational assistance
  const [roles, setRoles] = useState<SquadRoleInfo[]>([
    {
      role: "commander",
      name: "OmniStore Commander",
      model: "muse-spark-1.3",
      description: "Executive coordinator & micro-business digitization advisor.",
      capabilities: ["Pipeline Orchestration", "Merchant Advisory", "Dialogue Flow"],
    },
    {
      role: "planner",
      name: "Inventory Planner",
      model: "muse-spark-1.3",
      description: "Shelf layout optimization, stock analysis, and demand forecasting.",
      capabilities: ["Shelf Density", "Stock Velocity", "Pricing Matrix"],
    },
    {
      role: "coder",
      name: "Muse Code Engineer",
      model: "muse-code",
      description: "Agentic web code synthesis, PWA builder, and WhatsApp checkout integration.",
      capabilities: ["Next.js 14", "Tailwind CSS", "WhatsApp API", "Prisma/SQLite"],
    },
    {
      role: "desktop",
      name: "SAM 3.1 Spatial Eye",
      model: "sam-3.1",
      description: "Zero-shot visual perception, object masking, and coordinate localization.",
      capabilities: ["Physical Segmentation", "Bounding Boxes", "Shelf Frame OCR"],
    },
  ]);

  // Check health and roles on mount
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
        // Fallback default roles are already set
      }
    };

    checkConnection();
    fetchRoles();
    const interval = setInterval(checkConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  // Pipeline completion handler (from SAM 3.1 scan)
  const handlePipelineComplete = (result: PipelineResponse) => {
    setStoreSchema(result.store_schema);
    if (result.code_synthesis) {
      setCodeResponse(result.code_synthesis);
    }
    if (result.bounding_boxes && result.bounding_boxes.length > 0) {
      setSelectedBox(result.bounding_boxes[0]);
    }
    setStructuredOutput({
      summary: `Digitized ${result.store_schema.inventory.length} items for ${result.store_schema.store_title}.`,
      store_meta: {
        store_name: result.store_schema.store_title,
        currency: result.store_schema.currency,
        location: result.store_schema.location,
      },
      inventory: result.store_schema.inventory,
      entities_detected: result.bounding_boxes.map((b) => ({
        entity: b.label,
        box_id: b.box_id,
        relevance: "high",
        properties: { confidence: b.confidence },
      })),
      detailed_analysis: `SAM 3.1 segmented ${result.segments_found} regions. Muse Spark 1.3 cataloged items with localized ${result.store_schema.currency} pricing. Muse Code generated production storefront assets in ${result.processing_time_ms}ms.`,
      recommended_actions: [
        `Publish instant mobile storefront with WhatsApp checkout to ${result.store_schema.whatsapp_number}.`,
        "Print out localized QR code for physical stall placement.",
        "Track reorder thresholds via automated task queue.",
      ],
      confidence_score: 0.98,
      safety_assessment: "safe",
    });
  };

  // Muse Code generation handler
  const handleGenerateCode = async () => {
    if (!storeSchema) return;
    setIsGeneratingCode(true);
    try {
      const res = await generateStorefrontCode({
        store_schema: storeSchema,
        target_framework: "nextjs14_tailwind",
        features: [
          "mobile_first_grid",
          "whatsapp_checkout_integration",
          "inventory_counter",
          "pwa_offline_ready",
        ],
      });
      setCodeResponse(res);
      setActiveTab("storefront");
    } catch (err) {
      console.error("Code synthesis error:", err);
    } finally {
      setIsGeneratingCode(false);
    }
  };

  const inventoryCount = storeSchema?.inventory?.length || 0;

  return (
    <div className="flex flex-col min-h-screen bg-[#080d16] text-slate-100">
      <Navbar
        backendConnected={backendConnected}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        inventoryCount={inventoryCount}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 flex flex-col space-y-6">
        {/* TAB 1: PIPELINE STUDIO (SAM 3.1 Eyes + Muse Spark Brain) */}
        {activeTab === "pipeline" && (
          <div className="space-y-6">
            {/* Context & Info Banner */}
            <div className="bg-gradient-to-r from-emerald-950/40 via-cyan-950/30 to-indigo-950/40 border border-emerald-900/40 rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                    <span>Physical-to-Digital Micro-Commerce Pipeline</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-900/60 text-emerald-300 border border-emerald-700/50">
                      Active
                    </span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    1. <span className="text-cyan-400 font-mono">SAM 3.1</span> isolates items on stall shelves → 2. <span className="text-purple-400 font-mono">Muse Spark</span> infers pricing & catalog → 3. <span className="text-emerald-400 font-mono">Muse Code</span> builds web app.
                  </p>
                </div>
              </div>

              {inventoryCount > 0 && (
                <button
                  onClick={() => setActiveTab("storefront")}
                  className="flex items-center justify-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-emerald-900/40 transition-all self-start md:self-auto"
                >
                  <span>View Mobile Storefront ({inventoryCount} items)</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Main Studio Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column: SAM 3.1 Vision Canvas & Merchant Config (7 cols) */}
              <div className="lg:col-span-7 space-y-4">
                <SegmentCanvas
                  merchantContext={merchantContext}
                  onUpdateMerchantContext={setMerchantContext}
                  onPipelineComplete={handlePipelineComplete}
                  onSelectBox={setSelectedBox}
                />
              </div>

              {/* Right Column: Muse Spark Reasoning & Catalog Panel (5 cols) */}
              <div className="lg:col-span-5 h-[620px]">
                <MultimodalReasoningPanel
                  storeSchema={storeSchema}
                  structuredOutput={structuredOutput}
                  selectedBox={selectedBox}
                  onGenerateCode={handleGenerateCode}
                  isGeneratingCode={isGeneratingCode}
                />
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: STOREFRONT & CODE SYNTHESIS (Muse Code Hands) */}
        {activeTab === "storefront" && (
          <div className="space-y-4">
            <StorefrontPreview
              storeSchema={storeSchema}
              codeResponse={codeResponse}
            />
          </div>
        )}

        {/* TAB 3: ASYNC QUEUE & WEBHOOKS */}
        {activeTab === "queue" && (
          <div className="space-y-4">
            <TaskQueueWidget />
          </div>
        )}
      </main>

      {/* Floating Agent Assistant Toggle */}
      <div className="fixed bottom-6 right-6 z-40">
        {!chatOpen ? (
          <button
            onClick={() => setChatOpen(true)}
            className="flex items-center space-x-2 px-4 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-2xl shadow-2xl shadow-emerald-900/60 border border-emerald-400/30 transition-all transform hover:scale-105"
          >
            <Bot className="w-5 h-5 text-emerald-200" />
            <span className="text-xs font-bold">Ask AI Advisor</span>
          </button>
        ) : (
          <div className="w-[390px] sm:w-[460px] h-[580px] bg-[#0b101b] rounded-2xl border border-slate-800 shadow-2xl flex flex-col overflow-hidden backdrop-blur-xl animate-in fade-in slide-in-from-bottom-6 duration-200">
            {/* Chat Drawer Header */}
            <div className="p-3.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-100">OmniStore AI Assistant</h3>
                  <p className="text-[10px] text-slate-400">Powered by Muse Spark 1.3</p>
                </div>
              </div>
              <button
                onClick={() => setChatOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Chat Body */}
            <div className="flex-1 p-2 overflow-hidden">
              <ChatInterface
                activeRole={activeRole}
                onSelectRole={setActiveRole}
                roles={roles}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
