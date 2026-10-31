/**
 * Strongly-typed API client for Jenna AI Assistant FastAPI Backend Engine.
 * Integrates SAM 3.1 segmentation, Muse Spark reasoning, Web Streams streaming chat,
 * async job queues, and cross-agent memory.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ─── Interfaces & Schemas ───────────────────────────────────────────────────

export interface BoundingBox {
  box_id: string;
  label: string;
  confidence: number;
  bbox: [number, number, number, number]; // [ymin, xmin, ymax, xmax] (0.0 - 1.0)
  polygon_mask?: [number, number][];
  description?: string;
}

export interface SegmentCrop {
  box_id: string;
  label: string;
  crop_base64: string;
  mime_type?: string;
}

export interface SegmentResponse {
  success: boolean;
  model_used: string;
  image_width: number;
  image_height: number;
  bounding_boxes: BoundingBox[];
  crops: SegmentCrop[];
  processing_time_ms: number;
  total_segments: number;
}

export interface EntityObservation {
  entity: string;
  box_id?: string;
  properties: Record<string, any>;
  relevance: string;
}

export interface StructuredReasoningOutput {
  summary: string;
  entities_detected: EntityObservation[];
  detailed_analysis: string;
  recommended_actions: string[];
  confidence_score: number;
  safety_assessment: string;
}

export interface ReasonResponse {
  success: boolean;
  model_used: string;
  structured_output: StructuredReasoningOutput;
  raw_response?: string;
  processing_time_ms: number;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  name?: string;
  tool_calls?: any[];
  agent_role?: string;
}

export interface SquadRoleInfo {
  role: "commander" | "planner" | "coder" | "researcher" | "desktop";
  name: string;
  model: string;
  description: string;
  capabilities: string[];
}

export interface BackgroundJob {
  job_id: string;
  job_type: "segmentation" | "multimodal_reasoning" | "full_pipeline";
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface HealthStatus {
  status: string;
  assistant: string;
  version: string;
  active_providers: Record<string, boolean>;
}

// ─── API Client Methods ─────────────────────────────────────────────────────

/**
 * Fetch backend health status
 */
export async function getHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

/**
 * Fetch available squad roles and assigned models
 */
export async function getSquadRoles(): Promise<{ roles: SquadRoleInfo[] }> {
  const res = await fetch(`${API_BASE_URL}/agent/roles`);
  if (!res.ok) throw new Error(`Failed to fetch squad roles: ${res.statusText}`);
  return res.json();
}

/**
 * Stream real-time agent responses using the Web Streams API.
 */
export async function streamAgentChat({
  messages,
  agentRole = "commander",
  model,
  temperature = 0.7,
  onToken,
  onFinish,
  onError,
}: {
  messages: ChatMessage[];
  agentRole?: string;
  model?: string;
  temperature?: number;
  onToken: (token: string) => void;
  onFinish: (role: string) => void;
  onError: (error: Error) => void;
}): Promise<() => void> {
  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages,
          agent_role: agentRole,
          model,
          temperature,
          stream: true,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Chat request failed: ${response.status} ${response.statusText}`);
      }

      const body = response.body;
      if (!body) throw new Error("ReadableStream not supported on response");

      const reader = body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith("data: ")) continue;

          const dataPayload = trimmed.slice(6);
          if (dataPayload === "[DONE]") {
            onFinish(agentRole);
            return;
          }

          try {
            const parsed = JSON.parse(dataPayload);
            if (parsed.delta) {
              onToken(parsed.delta);
            }
            if (parsed.finish_reason === "stop") {
              onFinish(agentRole);
              return;
            }
          } catch (e) {
            console.warn("Failed to parse SSE line:", line, e);
          }
        }
      }

      onFinish(agentRole);
    } catch (err: any) {
      if (err.name !== "AbortError") {
        onError(err instanceof Error ? err : new Error(String(err)));
      }
    }
  })();

  return () => controller.abort();
}

/**
 * Segment image visual frame with SAM 3.1
 */
export async function segmentImage(
  imageBase64: string,
  prompt: string = "",
  confidenceThreshold: number = 0.25,
  maxSegments: number = 10
): Promise<SegmentResponse> {
  const res = await fetch(`${API_BASE_URL}/segment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_base64: imageBase64,
      prompt,
      confidence_threshold: confidenceThreshold,
      generate_crops: true,
      max_segments: maxSegments,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `SAM 3.1 segmentation failed: ${res.statusText}`);
  }

  return res.json();
}

/**
 * Upload file directly for SAM 3.1 segmentation
 */
export async function uploadAndSegment(
  file: File,
  prompt: string = "",
  confidenceThreshold: number = 0.25
): Promise<SegmentResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (prompt) formData.append("prompt", prompt);
  formData.append("confidence_threshold", confidenceThreshold.toString());

  const res = await fetch(`${API_BASE_URL}/segment/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload segmentation failed: ${res.statusText}`);
  }

  return res.json();
}

/**
 * Multimodal reasoning with Muse Spark 1.3
 */
export async function reasonMultimodal({
  prompt,
  segments,
  fullImageBase64,
  model = "muse-spark-1.3",
  temperature = 0.2,
}: {
  prompt: string;
  segments?: SegmentCrop[];
  fullImageBase64?: string;
  model?: string;
  temperature?: number;
}): Promise<ReasonResponse> {
  const res = await fetch(`${API_BASE_URL}/reason`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      segments,
      full_image_base64: fullImageBase64,
      model,
      temperature,
      structured_format: true,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Muse Spark reasoning failed: ${res.statusText}`);
  }

  return res.json();
}

/**
 * Background Task Queue Management
 */
export async function submitBackgroundJob(
  jobType: "segmentation" | "multimodal_reasoning" | "full_pipeline",
  payload: Record<string, any>,
  webhookUrl?: string
): Promise<BackgroundJob> {
  const res = await fetch(`${API_BASE_URL}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_type: jobType,
      payload,
      webhook_url: webhookUrl,
    }),
  });

  if (!res.ok) throw new Error(`Job submission failed: ${res.statusText}`);
  return res.json();
}

export async function getBackgroundJob(jobId: string): Promise<BackgroundJob> {
  const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Failed to fetch job ${jobId}: ${res.statusText}`);
  return res.json();
}

export async function listBackgroundJobs(limit: number = 20): Promise<BackgroundJob[]> {
  const res = await fetch(`${API_BASE_URL}/jobs?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to list jobs: ${res.statusText}`);
  return res.json();
}

/**
 * Cross-Agent Memory API
 */
export async function searchMemory(query: string, limit: number = 20) {
  const res = await fetch(`${API_BASE_URL}/memory/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });
  if (!res.ok) throw new Error(`Memory search failed: ${res.statusText}`);
  return res.json();
}

export async function getMemoryStats() {
  const res = await fetch(`${API_BASE_URL}/memory/stats`);
  if (!res.ok) throw new Error(`Failed to fetch memory stats: ${res.statusText}`);
  return res.json();
}
