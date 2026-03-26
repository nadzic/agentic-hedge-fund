import * as React from "react";

import { cn } from "@/lib/utils";

export function Textarea({
  className,
  ...props
}: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex min-h-28 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-offset-white placeholder:text-zinc-400 focus-visible:ring-2 focus-visible:ring-zinc-500",
        className,
      )}
      {...props}
    />
  );
}
