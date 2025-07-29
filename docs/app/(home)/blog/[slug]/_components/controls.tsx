"use client";
import { Check, Share } from "lucide-react";
import { useCopyButton } from "fumadocs-ui/utils/use-copy-button";
import { twMerge } from "tailwind-merge";

import { buttonVariants } from "@/src/components/ui/button";

export function Control({ url }: { url: string }): React.ReactElement {
  const [isChecked, onCopy] = useCopyButton(() => {
    void navigator.clipboard.writeText(`${window.location.origin}${url}`);
  });

  return (
    <button
      type="button"
      className={twMerge(
        buttonVariants({ className: "gap-2", variant: "secondary" }),
      )}
      onClick={onCopy}
    >
      {isChecked ? <Check className="size-4" /> : <Share className="size-4" />}
      {isChecked ? "Copied URL" : "Share Post"}
    </button>
  );
}
