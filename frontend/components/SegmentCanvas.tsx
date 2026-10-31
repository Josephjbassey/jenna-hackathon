"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Upload,
  Eye,
  Scan,
  Maximize2,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sliders,
} from "lucide-react";
import {
  BoundingBox,
  SegmentCrop,
  SegmentResponse,
  segmentImage,
  uploadAndSegment,
} from "@/lib/api";

interface SegmentCanvasProps {
  onSelectSegmentForReasoning: (crop: SegmentCrop, box: BoundingBox) => void;
  onFullSegmentationResult?: (result: SegmentResponse) => void;
}

// Built-in synthetic sample image (IDE + Terminal dashboard view) for instant testing
const SAMPLE_FRAME_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="%230f172a"/>
  <!-- Top bar -->
  <rect x="0" y="0" width="1280" height="48" fill="%231e293b"/>
  <circle cx="28" cy="24" r="7" fill="%23ef4444"/>
  <circle cx="48" cy="24" r="7" fill="%23f59e0b"/>
  <circle cx="68" cy="24" r="7" fill="%2310b981"/>
  <text x="100" y="30" fill="%2394a3b8" font-family="monospace" font-size="14">Jenna AI OS - Multi-Agent Unified Workspace</text>
  
  <!-- Left Editor Panel -->
  <rect x="24" y="68" width="760" height="440" rx="8" fill="%23111827" stroke="%23374151" stroke-width="2"/>
  <text x="44" y="104" fill="%2338bdf8" font-family="monospace" font-size="16" font-weight="bold">// Jenna Agent Squad Execution (FastAPI + SAM 3.1)</text>
  <text x="44" y="136" fill="%23a855f7" font-family="monospace" font-size="14">async def execute_multimodal_turn(frame: ImagePayload):</text>
  <text x="74" y="164" fill="%23cbd5e1" font-family="monospace" font-size="14">segments = await meta_service.segment_image(frame, prompt="UI regions")</text>
  <text x="74" y="192" fill="%23cbd5e1" font-family="monospace" font-size="14">reasoning = await meta_service.reason_multimodal(segments.crops)</text>
  <text x="74" y="220" fill="%2310b981" font-family="monospace" font-size="14">return {"status": "success", "analysis": reasoning.structured_output}</text>

  <!-- Right Preview Panel -->
  <rect x="804" y="68" width="452" height="440" rx="8" fill="%231e293b" stroke="%23374151" stroke-width="2"/>
  <text x="824" y="104" fill="%23f1f5f9" font-family="sans-serif" font-size="16" font-weight="bold">Live App Preview</text>
  <circle cx="1030" cy="240" r="70" fill="%2306b6d4" opacity="0.4"/>
  <circle cx="1030" cy="240" r="50" fill="%2306b6d4" opacity="0.8"/>
  <text x="965" y="340" fill="%2338bdf8" font-family="sans-serif" font-size="14">Interactive 3D Sphere</text>

  <!-- Bottom Console Terminal -->
  <rect x="24" y="528" width="1232" height="168" rx="8" fill="%23030712" stroke="%23374151" stroke-width="2"/>
  <text x="44" y="560" fill="%2322c55e" font-family="monospace" font-size="14">[jenna-agent] FastAPI server listening on http://localhost:8000</text>
  <text x="44" y="588" fill="%2338bdf8" font-family="monospace" font-size="14">[sam-3.1] Initialized visual segmentation engine (confidence threshold: 0.25)</text>
  <text x="44" y="616" fill="%23a855f7" font-family="monospace" font-size="14">[muse-spark] Ready for structured multimodal reasoning queries</text>
</svg>`;

export const SegmentCanvas: React.FC<SegmentCanvasProps> = ({
  onSelectSegmentForReasoning,
  onFullSegmentationResult,
}) => {
  const [imageSrc, setImageSrc] = useState<string>(SAMPLE_FRAME_SVG);
  const [prompt, setPrompt] = useState<string>("Locate code editor, live preview, and console terminal");
  const [confidence, setConfidence] = useState<number>(0.25);
  const [isSegmenting, setIsSegmenting] = useState<boolean>(false);
  const [segmentData, setSegmentData] = useState<SegmentResponse | null>(null);
  const [hoveredBoxId, setHoveredBoxId] = useState<string | null>(null);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Trigger initial segmentation on load
  useEffect(() => {
    runSegmentation(SAMPLE_FRAME_SVG);
  }, []);

  const runSegmentation = async (srcToUse: string) => {
    setIsSegmenting(true);
    setErrorMsg(null);
    try {
      const result = await segmentImage(srcToUse, prompt, confidence);
      setSegmentData(result);
      if (onFullSegmentationResult) {
        onFullSegmentationResult(result);
      }
    } catch (err: any) {
      console.error("Segmentation error:", err);
      setErrorMsg(err.message || "Failed to segment image with SAM 3.1");
    } finally {
      setIsSegmenting(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      setImageSrc(dataUrl);
      runSegmentation(dataUrl);
    };
    reader.readAsDataURL(file);
  };

  // Render canvas overlays
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !segmentData) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const w = canvas.width;
    const h = canvas.height;

    segmentData.bounding_boxes.forEach((box, idx) => {
      const [ymin, xmin, ymax, xmax] = box.bbox;
      const x = xmin * w;
      const y = ymin * h;
      const boxW = (xmax - xmin) * w;
      const boxH = (ymax - ymin) * h;

      const isHovered = hoveredBoxId === box.box_id;
      const isSelected = selectedBoxId === box.box_id;

      // Color scheme based on index
      const colors = ["#00f0ff", "#a855f7", "#38bdf8", "#10b981", "#f59e0b"];
      const baseColor = colors[idx % colors.length];

      // Draw bounding box
      ctx.lineWidth = isSelected ? 3 : isHovered ? 2.5 : 1.5;
      ctx.strokeStyle = isSelected ? "#ffffff" : baseColor;
      ctx.setLineDash(isHovered ? [4, 2] : []);
      ctx.strokeRect(x, y, boxW, boxH);

      // Draw filled translucent background
      ctx.fillStyle = isSelected
        ? "rgba(255, 255, 255, 0.15)"
        : isHovered
        ? `${baseColor}25`
        : `${baseColor}10`;
      ctx.fillRect(x, y, boxW, boxH);

      // Draw tag badge
      const tagText = `${box.label} (${Math.round(box.confidence * 100)}%)`;
      ctx.font = "bold 11px monospace";
      const textMetrics = ctx.measureText(tagText);
      const tagHeight = 18;
      const tagWidth = textMetrics.width + 12;

      ctx.fillStyle = isSelected ? "#0f172a" : baseColor;
      ctx.fillRect(x, Math.max(0, y - tagHeight), tagWidth, tagHeight);

      ctx.fillStyle = isSelected ? "#ffffff" : "#0b0f17";
      ctx.fillText(tagText, x + 6, Math.max(12, y - 5));
    });
  }, [segmentData, hoveredBoxId, selectedBoxId]);

  return (
    <div className="flex flex-col h-full bg-[#111726]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-4 shadow-xl">
      {/* Header controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <Scan className="w-4 h-4 text-cyan-400" />
          <h2 className="font-semibold text-sm text-slate-100">
            SAM 3.1 Visual Segmentation
          </h2>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-300">
            Meta Model
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept="image/*"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 transition-colors"
          >
            <Upload className="w-3.5 h-3.5 text-slate-400" />
            <span>Upload Frame</span>
          </button>

          <button
            onClick={() => runSegmentation(imageSrc)}
            disabled={isSegmenting}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-cyan-500 hover:bg-cyan-400 text-black font-semibold transition-all shadow-md shadow-cyan-500/20 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSegmenting ? "animate-spin" : ""}`} />
            <span>{isSegmenting ? "Segmenting..." : "Re-Segment"}</span>
          </button>
        </div>
      </div>

      {/* Prompt & Filter bar */}
      <div className="mt-3 flex items-center space-x-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter prompt to guide segmentation (e.g., 'find terminal window')..."
          className="flex-1 bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
        />
        <div className="flex items-center space-x-1.5 text-xs text-slate-400 font-mono px-2 py-1 bg-slate-900 border border-slate-800 rounded-lg">
          <Sliders className="w-3 h-3 text-cyan-400" />
          <span>Conf: {(confidence * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div
        ref={containerRef}
        className="relative mt-3 flex-1 min-h-[300px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center group"
      >
        {/* Background Image Element */}
        <img
          src={imageSrc}
          alt="Visual Frame"
          className="w-full h-full object-contain pointer-events-none select-none"
        />

        {/* Dynamic Overlay Canvas */}
        <canvas
          ref={canvasRef}
          width={1280}
          height={720}
          className="absolute inset-0 w-full h-full object-contain cursor-crosshair"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const clickX = (e.clientX - rect.left) / rect.width;
            const clickY = (e.clientY - rect.top) / rect.height;

            if (segmentData) {
              const clicked = segmentData.bounding_boxes.find((b) => {
                const [ymin, xmin, ymax, xmax] = b.bbox;
                return (
                  clickX >= xmin && clickX <= xmax && clickY >= ymin && clickY <= ymax
                );
              });
              if (clicked) {
                setSelectedBoxId(clicked.box_id);
                const matchingCrop = segmentData.crops.find(
                  (c) => c.box_id === clicked.box_id
                );
                if (matchingCrop) {
                  onSelectSegmentForReasoning(matchingCrop, clicked);
                }
              }
            }
          }}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;

            if (segmentData) {
              const hovered = segmentData.bounding_boxes.find((b) => {
                const [ymin, xmin, ymax, xmax] = b.bbox;
                return x >= xmin && x <= xmax && y >= ymin && y <= ymax;
              });
              setHoveredBoxId(hovered ? hovered.box_id : null);
            }
          }}
        />

        {/* Loading Spinner */}
        {isSegmenting && (
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm flex flex-col items-center justify-center z-20">
            <div className="w-10 h-10 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            <p className="mt-3 text-xs font-mono text-cyan-300">
              SAM 3.1 extracting segment boundaries...
            </p>
          </div>
        )}
      </div>

      {/* Segment Crops Tray */}
      <div className="mt-3 pt-3 border-t border-slate-800">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span>Detected Regions ({segmentData?.bounding_boxes.length || 0})</span>
          <span className="font-mono text-[11px] text-cyan-400">
            Click segment to reason with Muse Spark
          </span>
        </div>

        <div className="flex items-center space-x-2 overflow-x-auto pb-1">
          {segmentData?.bounding_boxes.map((box) => {
            const matchingCrop = segmentData.crops.find((c) => c.box_id === box.box_id);
            const isSelected = selectedBoxId === box.box_id;

            return (
              <button
                key={box.box_id}
                onClick={() => {
                  setSelectedBoxId(box.box_id);
                  if (matchingCrop) {
                    onSelectSegmentForReasoning(matchingCrop, box);
                  }
                }}
                onMouseEnter={() => setHoveredBoxId(box.box_id)}
                onMouseLeave={() => setHoveredBoxId(null)}
                className={`flex-shrink-0 flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                  isSelected
                    ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-sm"
                    : "bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-300"
                }`}
              >
                <Sparkles className="w-3 h-3 text-cyan-400" />
                <span className="max-w-[140px] truncate">{box.label}</span>
                <span className="text-[10px] font-mono text-slate-400">
                  {(box.confidence * 100).toFixed(0)}%
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
