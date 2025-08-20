import { z } from "zod";

export const EdgeSpec = z.object({
  target: z.string(),
  when: z.string().nullish(),
  id: z.string().nullish(),
  depends: z.array(z.string()).nullish(),
});

export type TEdgeSpec = z.infer<typeof EdgeSpec>;
