import { rimraf } from "rimraf";
import * as Python from "fumadocs-python";
import * as fs from "node:fs/promises";

const jsonPath = "../python/library_api_info.json";

async function generate() {
  const out = "content/docs/python";

  const content = JSON.parse((await fs.readFile(jsonPath)).toString());
  console.log(content);
  for (const [libName, lib] of Object.entries(content)) {
    const libPath = out + "/" + libName;
    await rimraf(libPath);
    const converted = Python.convert(lib, {
      baseUrl: `/docs/python/`,
    });
    await Python.write(converted, {
      outDir: libPath,
    });
  }
}

void generate();
