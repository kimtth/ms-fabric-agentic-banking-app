import { cp, rm } from 'fs/promises';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(scriptDir, '..', '..');
const backendStatic = join(repoRoot, 'backend', 'static');
const frontendOut = join(repoRoot, 'frontend', 'out');

await rm(backendStatic, { recursive: true, force: true });
await cp(frontendOut, backendStatic, { recursive: true });
console.log(`✓ Copied ${frontendOut} → ${backendStatic}`);
