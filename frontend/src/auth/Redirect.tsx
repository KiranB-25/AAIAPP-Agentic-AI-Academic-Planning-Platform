import { useEffect } from "react";

import { navigate } from "./routes";

export function Redirect({ to }: { to: string }) {
  useEffect(() => {
    navigate(to);
  }, [to]);

  return null;
}
