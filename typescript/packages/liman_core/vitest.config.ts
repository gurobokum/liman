import { defineConfig, mergeConfig } from "vitest/config";
import baseConfig from "../../vitest.config";
import path from "path";

export default mergeConfig(
  baseConfig,
  defineConfig({
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
  }),
);
