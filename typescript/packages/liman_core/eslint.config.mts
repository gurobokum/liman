import prettier from "eslint-config-prettier";
import { defineConfig } from "eslint/config";

import baseConfig from "../../eslint.config.mjs";

export default defineConfig([...baseConfig, prettier]);
