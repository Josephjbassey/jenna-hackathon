"use client";

import React, { useState, useEffect } from "react";
import { SegmentCanvas } from "@/components/SegmentCanvas";
import { MultimodalReasoningPanel } from "@/components/MultimodalReasoningPanel";
import { StorefrontPreview } from "@/components/StorefrontPreview";
import { TaskQueueWidget } from "@/components/TaskQueueWidget";
import { ChatInterface } from "@/components/ChatInterface";
import { STALL_PRESETS, StallPreset } from "@/lib/presets";
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
  Sparkles,
  Store,
  Layers,
  Code2,
  X,
  ChevronRight,
  Camera,
  Tag,
  Smartphone,
  PhoneCall,
  Terminal,
  Activity,
  ArrowRight,
  HelpCircle,
  CheckCircle2,
} from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"demo" | "storefront" | "architecture">("demo");
  const [activePreset, setActivePreset] = useState<StallPreset>(STALL_PRESETS[0]);
  const [backendConnected, setBackendConnected] = useState<boolean>(true);
  const [chatOpen, setChatOpen] = useState<boolean>(false);
  const [activeRole, setActiveRole] = useState<string>("commander");
  const [isGeneratingCode, setIsGeneratingCode] = useState<boolean>(false);

  // Merchant context
  const [merchantContext, setMerchantContext] = useState<MerchantContext>({
    store_name: STALL_PRESETS[0].name,
    currency: STALL_PRESETS[0].currency,
    location: STALL_PRESETS[0].location,
    whatsapp_number: STALL_PRESETS[0].whatsapp_number,
  });

  // State populated through 3-model pipeline
  const [selectedBox, setSelectedBox] = useState<BoundingBox | null>(STALL_PRESETS[0].boxes[0]);
  const [storeSchema, setStoreSchema] = useState<StorefrontSchema | null>(STALL_PRESETS[0].schema);
  const [structuredOutput, setStructuredOutput] = useState<StructuredReasoningOutput | null>({
    summary: `Digitized ${STALL_PRESETS[0].schema.inventory.length} items for ${STALL_PRESETS[0].name}.`,
    store_meta: {
      store_name: STALL_PRESETS[0].name,
      currency: STALL_PRESETS[0].currency,
      location: STALL_PRESETS[0].location,
    },
    inventory: STALL_PRESETS[0].schema.inventory,
    entities_detected: STALL_PRESETS[0].boxes.map((b) => ({
      entity: b.label,
      box_id: b.box_id,
      relevance: "high",
      properties: { confidence: b.confidence },
    })),
    detailed_analysis: `SAM 3.1 segmented ${STALL_PRESETS[0].boxes.length} shelf regions. Muse Spark 1.3 priced items in ${STALL_PRESETS[0].currency}. Muse Code generated mobile storefront with WhatsApp checkout.`,
    recommended_actions: [
      `Share instant mobile storefront link with customers on WhatsApp (${STALL_PRESETS[0].whatsapp_number}).`,
      "Print QR code poster for physical stall display.",
      "Sync stock counts with daily reorder thresholds.",
    ],
    confidence_score: 0.98,
    safety_assessment: "safe",
  });
  const [codeResponse, setCodeResponse] = useState<CodeGenerateResponse | null>(null);

  // Switch stall preset
  const handleSelectPreset = (preset: StallPreset) => {
    setActivePreset(preset);
    setMerchantContext({
      store_name: preset.name,
      currency: preset.currency,
      location: preset.location,
      whatsapp_number: preset.whatsapp_number,
    });
    setStoreSchema(preset.schema);
    setSelectedBox(preset.boxes[0]);
    setStructuredOutput({
      summary: `Digitized ${preset.schema.inventory.length} items for ${preset.name}.`,
      store_meta: {
        store_name: preset.name,
        currency: preset.currency,
        location: preset.location,
      },
      inventory: preset.schema.inventory,
      entities_detected: preset.boxes.map((b) => ({
        entity: b.label,
        box_id: b.box_id,
        relevance: "high",
        properties: { confidence: b.confidence },
      })),
      detailed_analysis: `SAM 3.1 identified ${preset.boxes.length} products. Muse Spark priced inventory in ${preset.currency}. Muse Code prepared mobile storefront.`,
      recommended_actions: [
        `Publish mobile storefront to WhatsApp (${preset.whatsapp_number}).`,
        "Print out localized QR code for stall placement.",
      ],
      confidence_score: 0.98,
      safety_assessment: "safe",
    });
  };

  // Agent roles
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

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const health = await getHealth();
        setBackendConnected(health.status === "healthy" || health.status === "ok");
      } catch (err) {
        setBackendConnected(false);
      }
    };
    checkConnection();
    const interval = setInterval(checkConnection, 12000);
    return () => clearInterval(interval);
  }, []);

  const handlePipelineComplete = (result: PipelineResponse) => {
    setStoreSchema(result.store_schema);
    if (result.code_synthesis) {
      setCodeResponse(result.code_synthesis);
    }
    if (result.bounding_boxes && result.bounding_boxes.length > 0) {
      setSelectedBox(result.bounding_boxes[0]);
    }
  };

  const handleGenerateCode = async () => {
    if (!storeSchema) return;
    setIsGeneratingCode(true);
    try {
      const res = await generateStorefrontCode({
        store_schema: storeSchema,
        target_framework: "nextjs14_tailwind",
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
    <div className="flex flex-col min-h-screen bg-[#080a0f] text-slate-100">
      {/* Top Simple Navigation */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#0c0f16]/95 backdrop-blur-md px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Store className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-sm tracking-tight text-white">OmniStore AI</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-800/50 text-emerald-300">
                  Build for Your World
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Snap a stall photo → Get a WhatsApp online store in seconds
              </p>
            </div>
          </div>

          {/* Simple Tab Switcher */}
          <div className="flex items-center space-x-1.5 bg-[#141822] p-1 rounded-xl border border-white/10">
            <button
              onClick={() => setActiveTab("demo")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "demo"
                  ? "bg-white text-black shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Interactive Studio</span>
            </button>

            <button
              onClick={() => setActiveTab("storefront")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "storefront"
                  ? "bg-white text-black shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Smartphone className="w-3.5 h-3.5" />
              <span>Customer Storefront ({inventoryCount})</span>
            </button>

            <button
              onClick={() => setActiveTab("architecture")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "architecture"
                  ? "bg-white text-black shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Under The Hood (Meta AI)</span>
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* HERO SECTION: Anyone understands this immediately */}
        <div className="bg-[#0f131c] border border-white/10 rounded-2xl p-5 sm:p-6 relative overflow-hidden">
          <div className="max-w-3xl space-y-2">
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-800/60 text-emerald-300 text-[11px] font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>How It Works: 1. Photo → 2. AI Pricing → 3. WhatsApp Store</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Turn any street stall or kiosk into an online store in seconds.
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Designed for market stall owners and small merchants in emerging economies who don&apos;t have desktop computers or barcodes. Meta&apos;s multimodal models isolate products from a photo, price them in local currency, and generate a mobile store with 1-click WhatsApp orders.
            </p>
          </div>

          {/* Quick 1-Click Preset Switcher */}
          <div className="mt-5 pt-4 border-t border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
              Try a sample market stall:
            </span>
            <div className="flex flex-wrap items-center gap-2">
              {STALL_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset)}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-all flex items-center space-x-1.5 ${
                    activePreset.id === preset.id
                      ? "bg-emerald-500 text-black font-bold border-emerald-400 shadow-md"
                      : "bg-[#161c28] text-slate-300 border-white/10 hover:border-white/30"
                  }`}
                >
                  <span>{preset.badge}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* TAB 1: MAIN INTERACTIVE STUDIO (3 Visual Steps) */}
        {activeTab === "demo" && (
          <div className="space-y-4">
            {/* 3 Step Process Bar */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-[#0f131c] border border-white/10 flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold text-xs">
                  1
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white flex items-center space-x-1.5">
                    <span>Physical Stall Photo</span>
                    <span className="text-[10px] font-mono text-cyan-400">(SAM 3.1)</span>
                  </h3>
                  <p className="text-[11px] text-slate-400">Isolates physical goods &amp; stock</p>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-[#0f131c] border border-white/10 flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 font-bold text-xs">
                  2
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white flex items-center space-x-1.5">
                    <span>Fair Local Pricing</span>
                    <span className="text-[10px] font-mono text-amber-400">(Muse Spark)</span>
                  </h3>
                  <p className="text-[11px] text-slate-400">Calculates market rates in {merchantContext.currency}</p>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-[#0f131c] border border-white/10 flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs">
                  3
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white flex items-center space-x-1.5">
                    <span>1-Click WhatsApp Store</span>
                    <span className="text-[10px] font-mono text-emerald-400">(Muse Code)</span>
                  </h3>
                  <p className="text-[11px] text-slate-400">Instant web app + WhatsApp checkout</p>
                </div>
              </div>
            </div>

            {/* Split Screen Studio: Step 1 (Left) & Step 2 (Right) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column: Visual Perception (Step 1) */}
              <div className="lg:col-span-7">
                <SegmentCanvas
                  merchantContext={merchantContext}
                  onUpdateMerchantContext={setMerchantContext}
                  onPipelineComplete={handlePipelineComplete}
                  onSelectBox={setSelectedBox}
                />
              </div>

              {/* Right Column: Reasoning & Pricing Catalog (Step 2) */}
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

        {/* TAB 2: STOREFRONT & PHONE SIMULATOR (Step 3) */}
        {activeTab === "storefront" && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-[#0f131c] border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-white">Live Customer Experience (Smartphone Simulator)</h2>
                <p className="text-xs text-slate-400">
                  This is the exact mobile web store generated by Muse Code. Try adding items to the cart and tapping &quot;Order on WhatsApp&quot;!
                </p>
              </div>
              <button
                onClick={() => setActiveTab("demo")}
                className="px-3 py-1.5 bg-[#161c28] hover:bg-[#202838] text-slate-200 border border-white/10 rounded-lg text-xs font-semibold self-start sm:self-auto"
              >
                ← Back to Stall Scanner
              </button>
            </div>

            <StorefrontPreview
              storeSchema={storeSchema}
              codeResponse={codeResponse}
            />
          </div>
        )}

        {/* TAB 3: UNDER THE HOOD / META AI ARCHITECTURE (For Judges) */}
        {activeTab === "architecture" && (
          <div className="space-y-6">
            <div className="p-5 rounded-2xl bg-[#0f131c] border border-white/10 space-y-4">
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <span>Meta AI 3-Model Pipeline Architecture</span>
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed">
                OmniStore AI replaces manual e-commerce data entry with a 3-stage autonomous agent loop:
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div className="p-4 rounded-xl bg-[#141822] border border-white/10 space-y-2">
                  <span className="text-[10px] font-mono uppercase text-cyan-400 block font-bold">
                    1. SAM 3.1 (Eyes)
                  </span>
                  <h3 className="text-xs font-bold text-white">Visual Perception &amp; Segmentation</h3>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Zero-shot detection of goods on crowded physical shelves. Outputs normalized bounding box coordinates [ymin, xmin, ymax, xmax], polygon contours, and visual crops.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#141822] border border-white/10 space-y-2">
                  <span className="text-[10px] font-mono uppercase text-amber-400 block font-bold">
                    2. Muse Spark 1.3 (Brain)
                  </span>
                  <h3 className="text-xs font-bold text-white">Cognitive Reasoning &amp; Pricing</h3>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Multimodal grounding in emerging market commerce. Infers product names, counts stock quantities from masks, assigns fair market prices in local currency, and formats structured StorefrontSchema JSON.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#141822] border border-white/10 space-y-2">
                  <span className="text-[10px] font-mono uppercase text-emerald-400 block font-bold">
                    3. Muse Code (Hands)
                  </span>
                  <h3 className="text-xs font-bold text-white">Agentic Web Synthesis</h3>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Programmatically writes mobile-first Next.js 14 App Router storefront code (app/page.tsx), a WhatsApp checkout API handler (checkout/route.ts), and Prisma database models.
                  </p>
                </div>
              </div>
            </div>

            {/* Task Queue Widget for long-running batch jobs */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider font-mono text-slate-400">
                Async Background Queue &amp; Webhooks
              </h3>
              <TaskQueueWidget />
            </div>
          </div>
        )}
      </main>

      {/* Floating Tactical Assistant */}
      <div className="fixed bottom-6 right-6 z-40">
        {!chatOpen ? (
          <button
            onClick={() => setChatOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-[#161c28] hover:bg-[#202838] text-white rounded-xl shadow-2xl border border-white/20 active:translate-y-0.5 transition-all"
          >
            <Bot className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-bold">Ask AI Advisor</span>
          </button>
        ) : (
          <div className="w-[390px] sm:w-[460px] h-[580px] bg-[#0c0f16] rounded-2xl border border-white/20 shadow-2xl flex flex-col overflow-hidden backdrop-blur-xl">
            <div className="p-3 bg-[#141822] border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Bot className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-white">OmniStore AI Assistant</h3>
              </div>
              <button
                onClick={() => setChatOpen(false)}
                className="p-1 text-slate-400 hover:text-white rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
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
