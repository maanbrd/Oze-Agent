#!/usr/bin/env node

import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { spawnSync } from "node:child_process";
import { basename, resolve } from "node:path";

const environment = process.argv[2] ?? "preview";
const target = process.argv[3] ?? ".env.local";
const targetPath = resolve(process.cwd(), target);

if (existsSync(targetPath)) {
  const backupDir = "/tmp/agent-oze-env-backups";
  mkdirSync(backupDir, { recursive: true });

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const backupPath = `${backupDir}/${basename(target)}.${stamp}.backup`;
  copyFileSync(targetPath, backupPath);
  console.log(`Backed up ${target} to ${backupPath}`);
}

const result = spawnSync(
  "npx",
  ["vercel", "env", "pull", target, "--environment", environment, "--yes"],
  {
    cwd: process.cwd(),
    stdio: "inherit",
  },
);

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

if ((result.status ?? 1) !== 0) {
  process.exit(result.status ?? 1);
}

if (existsSync(targetPath)) {
  const envLines = readFileSync(targetPath, "utf8").split(/\r?\n/);
  let removedBlankLines = 0;
  const cleaned = envLines.filter((line) => {
    const match = line.match(/^([A-Z0-9_]+)=(.*)$/);
    if (!match) {
      return true;
    }

    const [, , value] = match;
    const isBlank = value === "" || value === `""` || value === "''";
    if (isBlank) {
      removedBlankLines += 1;
    }

    return !isBlank;
  });
  writeFileSync(targetPath, `${cleaned.join("\n").replace(/\n+$/, "")}\n`);
  console.log(`Removed ${removedBlankLines} blank entries from local env file`);
}

process.exit(0);
