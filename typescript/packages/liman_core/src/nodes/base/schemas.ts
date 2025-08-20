import { z } from "zod";

export const NodeState = z.object({
  kind: z.string(),
  name: z.string(),
  context: z.object().default({}),
});

export type TNodeState = z.infer<typeof NodeState>;
