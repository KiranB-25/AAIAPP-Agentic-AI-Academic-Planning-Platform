import { useEffect, useState } from "react";

import { getHealth } from "../services/health-service";

type HealthState = "loading" | "connected" | "error";

interface UseHealthCheckResult {
  state: HealthState;
  message: string;
}

export function useHealthCheck(): UseHealthCheckResult {
  const [result, setResult] = useState<UseHealthCheckResult>({
    state: "loading",
    message: "Checking backend availability…",
  });

  useEffect(() => {
    let isCurrent = true;

    getHealth()
      .then((response) => {
        if (isCurrent && response.status === "ok") {
          setResult({ state: "connected", message: "Connected" });
        }
      })
      .catch(() => {
        if (isCurrent) {
          setResult({ state: "error", message: "Connection unavailable" });
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  return result;
}
