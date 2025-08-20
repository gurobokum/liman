import { z } from "zod";

export const BaseSpec = z.object({
  kind: z.string(),
  name: z.string(),
});

export type TBaseSpec = z.infer<typeof BaseSpec>;
