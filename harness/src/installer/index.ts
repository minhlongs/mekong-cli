/**
 * AgentKit Installer Layer
 * OS detection, SHA-256 manifest verification, idempotent installation.
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as crypto from "crypto";

export interface InstallerConfig {
  targetDir: string;
  channel: "stable" | "beta" | "nightly";
  yes: boolean;
  excludeSkills: string[];
  skillsOnly: boolean;
}

export interface Manifest {
  version: string;
  channel: string;
  sha256: string;
  files: ManifestFile[];
  postInstall?: string[];
}

export interface ManifestFile {
  path: string;
  sha256: string;
  mode?: number;
}

export class OsDetector {
  static detect() {
    const p = os.platform();
    const a = os.arch();
    let ext = ".tar.gz";
    if (p === "win32") ext = ".zip";
    else if (p === "darwin" && a === "arm64") ext = "-aarch64.tar.gz";
    else if (p === "darwin" && a === "x64") ext = "-x86_64.tar.gz";
    return { platform: p, arch: a, ext };
  }

  static isSupported(): boolean {
    const { platform } = this.detect();
    return ["darwin", "linux", "win32"].includes(platform);
  }

  static label(): string {
    const { platform, arch, ext } = this.detect();
    return platform + "-" + arch + ext;
  }
}

export class ManifestVerifier {
  static async verify(filePath: string, expectedSha256: string): Promise<boolean> {
    return new Promise((resolve) => {
      const hash = crypto.createHash("sha256");
      const stream = fs.createReadStream(filePath);
      stream.on("data", (chunk) => hash.update(chunk));
      stream.on("end", () => {
        resolve(hash.digest("hex") === expectedSha256.toLowerCase());
      });
      stream.on("error", () => resolve(false));
    });
  }

  static async verifyDir(dir: string, manifest: Manifest): Promise<{
    ok: boolean;
    failed: string[];
  }> {
    const failed: string[] = [];
    for (const file of manifest.files) {
      const full = path.join(dir, file.path);
      if (!fs.existsSync(full)) {
        failed.push(file.path + " (missing)");
        continue;
      }
      const ok = await this.verify(full, file.sha256);
      if (!ok) failed.push(file.path + " (hash mismatch)");
    }
    return { ok: failed.length === 0, failed };
  }
}

export class IdempotentInstaller {
  private sentinelFile: string;

  constructor(private config: InstallerConfig) {
    this.sentinelFile = path.join(config.targetDir, ".agentkit-installed");
  }

  isInstalled(): boolean {
    return fs.existsSync(this.sentinelFile);
  }

  markInstalled(version: string): void {
    fs.writeFileSync(
      this.sentinelFile,
      JSON.stringify({ version, at: new Date().toISOString(), channel: this.config.channel })
    );
  }

  shouldSkip(path: string): boolean {
    if (this.config.skillsOnly) {
      return !path.includes("/skills/") && !path.includes("skills");
    }
    for (const exclude of this.config.excludeSkills) {
      if (path.includes(exclude)) return true;
    }
    return false;
  }

  async install(manifest: Manifest): Promise<{ installed: string[]; skipped: string[] }> {
    const installed: string[] = [];
    const skipped: string[] = [];

    if (!this.config.yes && this.isInstalled()) {
      const existing = JSON.parse(fs.readFileSync(this.sentinelFile, "utf-8"));
      throw new Error(
        `Already installed (v${existing.version}). Pass --yes to reinstall.`
      );
    }

    for (const file of manifest.files) {
      if (this.shouldSkip(file.path)) {
        skipped.push(file.path);
        continue;
      }
      const dest = path.join(this.config.targetDir, file.path);
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      if (file.mode) fs.chmodSync(dest, file.mode);
      installed.push(file.path);
    }

    this.markInstalled(manifest.version);

    if (manifest.postInstall) {
      for (const cmd of manifest.postInstall) {
        try {
          const { execSync } = await import("child_process");
          execSync(cmd, { cwd: this.config.targetDir, stdio: "pipe" });
        } catch {
          // post-install commands are best-effort
        }
      }
    }

    return { installed, skipped };
  }
}

export class InstallerLayer {
  async init(config: InstallerConfig): Promise<{ ok: boolean; message: string }> {
    if (!OsDetector.isSupported()) {
      return { ok: false, message: "Unsupported OS: " + OsDetector.detect().platform };
    }

    fs.mkdirSync(config.targetDir, { recursive: true });
    const installer = new IdempotentInstaller(config);

    const manifest = this.buildManifest(config);
    const verification = await ManifestVerifier.verifyDir(config.targetDir, manifest);

    if (!verification.ok) {
      return {
        ok: false,
        message: "Verification failed: " + verification.failed.join(", "),
      };
    }

    const result = await installer.install(manifest);
    return {
      ok: true,
      message:
        "Installed " + result.installed.length + " files, skipped " + result.skipped.length,
    };
  }

  private buildManifest(config: InstallerConfig): Manifest {
    const files: ManifestFile[] = [];
    const src = path.join(config.targetDir, ".claude");

    if (!config.skillsOnly) {
      files.push({ path: ".claude/commands/", sha256: "dir", mode: 0o755 });
      files.push({ path: ".claude/agents/", sha256: "dir", mode: 0o755 });
      files.push({ path: ".claude/settings.json", sha256: "touch" });
    }
    if (!config.excludeSkills.includes("all")) {
      files.push({ path: ".claude/skills/", sha256: "dir", mode: 0o755 });
    }

    return {
      version: "1.0.0",
      channel: config.channel,
      sha256: crypto.createHash("sha256").update(JSON.stringify(files)).digest("hex"),
      files,
    };
  }
}
