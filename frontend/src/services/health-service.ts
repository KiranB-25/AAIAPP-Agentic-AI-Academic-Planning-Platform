import { get } from "./api-client";
import type { HealthResponse } from "../types/api";

export function getHealth(): Promise<HealthResponse> {
  return get<HealthResponse>("/api/health/");
}
