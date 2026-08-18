import { CircleAlert, CircleCheck, LoaderCircle } from "lucide-react";

import { Card } from "./ui/card";
import { useHealthCheck } from "../hooks/useHealthCheck";

export function ApiStatus() {
  const { state, message } = useHealthCheck();
  const icon = state === "loading"
    ? <LoaderCircle className="size-5 animate-spin text-muted-foreground" aria-hidden="true" />
    : state === "connected"
      ? <CircleCheck className="size-5 text-success" aria-hidden="true" />
      : <CircleAlert className="size-5 text-destructive" aria-hidden="true" />;

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Application status</p>
          <h2 className="mt-1 text-lg font-semibold">Backend API</h2>
        </div>
        <div className="flex items-center gap-2 text-sm font-medium" aria-live="polite">
          {icon}
          <span>{message}</span>
        </div>
      </div>
    </Card>
  );
}
