"use client";

import React, { useState } from "react";
import {
  Brain,
  CheckCircle2,
  AlertTriangle,
  Send,
  Code2,
  ListChecks,
  ChevronDown,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import {
  BoundingBox,
  SegmentCrop,
  ReasonResponse,
  StructuredReasoningOutput,
  reasonMultimodal,
} from "@/lib/api";

interface MultimodalReasoningPanelProps {
  selectedCrop: SegmentCrop | null;
  selectedBox: BoundingBox | null;
  initialReasoning?: ReasonResponse | null;
}

export const MultimodalReasoningPanel: React.FC<MultimodalReasoningPanelProps> = ({
  selectedCrop,
  selectedBox,
  initialReasoning,
}) => {
  const [prompt, setPrompt] = useState<string>(
    "Analyze the selected segment, evaluate state integrity, and prescribe next action."
  );
  const [isReasoning, setIsReasoning] = useState<boolean>(false);
  const [reasonData, setReasonData] = useState<ReasonResponse | null>(
    initialReasoning || null
  );
  const [showRawJson, setShowRawJson] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleRunReasoning = async () => {
    setIsReasoning(true);
    setErrorMsg(null);
    try {
      const resp = await reasonMultimodal({
        prompt,
        segments: selectedCrop ? [selectedCrop] : undefined,
        model: "muse-spark-1.3",
      });
      setReasonData(resp);
    } catch (err: any) {
      console.error("Reasoning error:", err);
      setErrorMsg(err.message || "Failed to execute Muse Spark reasoning");
    } finally {
      setIsReasoning(false);
    }
  };

  const output: StructuredReasoningOutput | undefined = reasonData?.structured_output;

  return (
    <div className="flex flex-col h-full bg-[#111726]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <Brain className="w-4 h-4 text-purple-400" />
          <h2 className="font-semibold text-sm text-slate-100">
            Muse Spark 1.3 Multimodal Reasoning
          </h2>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-950 border border-purple-800 text-purple-300">
          Structured Pydantic Output
        </span>
      </div>

      {/* Target Segment Context Pill */}
      {selectedBox && (
        <div className="mt-3 p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span className="text-xs font-semibold text-slate-200">
              Active Segment: {selectedBox.label}
            </span>
          </div>
          <span className="text-[11px] font-mono text-cyan-400">
            ID: {selectedBox.box_id}
          </span>
        </div>
      )}

      {/* Prompt Input Form */}
      <div className="mt-3 flex items-center space-x-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ask Muse Spark to analyze this visual context..."
          className="flex-1 bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
        />
        <button
          onClick={handleRunReasoning}
          disabled={isReasoning}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-purple-600 hover:bg-purple-500 text-white font-semibold transition-all shadow-md shadow-purple-500/20 disabled:opacity-50"
        >
          <Sparkles className={`w-3.5 h-3.5 ${isReasoning ? "animate-spin" : ""}`} />
          <span>{isReasoning ? "Thinking..." : "Reason"}</span>
        </button>
      </div>

      {/* Reasoning Output Display */}
      <div className="mt-4 flex-1 overflow-y-auto space-y-3 pr-1">
        {errorMsg && (
          <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-400" />
            <span>{errorMsg}</span>
          </div>
        )}

        {output ? (
          <>
            {/* Executive Summary Card */}
            <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-purple-300 uppercase tracking-wider font-mono">
                  Executive Summary
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-400">
                  Confidence: {(output.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed">
                {output.summary}
              </p>
            </div>

            {/* Detailed Analysis */}
            <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-xl">
              <span className="text-xs font-semibold text-cyan-300 uppercase tracking-wider font-mono block mb-1.5">
                Detailed Analysis
              </span>
              <p className="text-xs text-slate-300 leading-relaxed">
                {output.detailed_analysis}
              </p>
            </div>

            {/* Entities Detected */}
            {output.entities_detected && output.entities_detected.length > 0 && (
              <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-xl">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono block mb-2">
                  Entities Observed ({output.entities_detected.length})
                </span>
                <div className="space-y-1.5">
                  {output.entities_detected.map((e, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                        <span className="font-medium text-slate-200">{e.entity}</span>
                      </div>
                      <span className="text-[10px] font-mono text-purple-300">
                        {e.relevance} priority
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Action Items */}
            {output.recommended_actions && output.recommended_actions.length > 0 && (
              <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-xl">
                <div className="flex items-center space-x-2 mb-2">
                  <ListChecks className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-xs font-semibold text-emerald-300 uppercase tracking-wider font-mono">
                    Prescribed Actions
                  </span>
                </div>
                <ul className="space-y-1.5">
                  {output.recommended_actions.map((act, idx) => (
                    <li
                      key={idx}
                      className="flex items-start space-x-2 text-xs text-slate-300"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>{act}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Raw JSON Inspector */}
            <div className="border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => setShowRawJson(!showRawJson)}
                className="w-full flex items-center justify-between p-2.5 bg-slate-900/80 hover:bg-slate-850 text-xs text-slate-400 font-mono transition-colors"
              >
                <div className="flex items-center space-x-1.5">
                  <Code2 className="w-3.5 h-3.5 text-slate-400" />
                  <span>Inspect Validated JSON Schema</span>
                </div>
                {showRawJson ? (
                  <ChevronDown className="w-3.5 h-3.5" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5" />
                )}
              </button>
              {showRawJson && (
                <pre className="p-3 bg-slate-950 text-[11px] font-mono text-cyan-300 overflow-x-auto max-h-48">
                  {JSON.stringify(output, null, 2)}
                </pre>
              )}
            </div>
          </>
        ) : (
          <div className="h-48 flex flex-col items-center justify-center text-slate-500 text-xs text-center border border-dashed border-slate-800 rounded-xl p-4">
            <Brain className="w-8 h-8 text-slate-600 mb-2" />
            <p className="text-slate-400 font-medium">Ready for Multimodal Reasoning</p>
            <p className="text-[11px] text-slate-500 mt-1">
              Select a segment or frame and click &ldquo;Reason&rdquo; to execute Muse Spark 1.3
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
