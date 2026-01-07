/**
 * Shared CLI utilities for add-skill, add-command, and add-agent.
 */

import * as path from 'node:path';
import * as os from 'node:os';
import ora, { type Ora } from 'ora';
import chalk from 'chalk';

/**
 * Parse '<username>/<name>' into components.
 *
 * @param ref - Resource reference in format 'username/name'
 * @returns Tuple of [username, name]
 * @throws Error if the format is invalid
 */
export function parseResourceRef(ref: string): [string, string] {
  const parts = ref.split('/');
  if (parts.length !== 2) {
    throw new Error(`Invalid format: '${ref}'. Expected: <username>/<name>`);
  }
  const [username, name] = parts;
  if (!username || !name) {
    throw new Error(`Invalid format: '${ref}'. Expected: <username>/<name>`);
  }
  return [username, name];
}

/**
 * Get the destination directory for a resource.
 *
 * @param resourceSubdir - The subdirectory name (e.g., "skills", "commands", "agents")
 * @param globalInstall - If true, install to ~/.claude/, else to ./.claude/
 * @returns Path to the destination directory
 */
export function getDestination(
  resourceSubdir: string,
  globalInstall: boolean
): string {
  let base: string;
  if (globalInstall) {
    base = path.join(os.homedir(), '.claude');
  } else {
    base = path.join(process.cwd(), '.claude');
  }
  return path.join(base, resourceSubdir);
}

/**
 * Create a spinner for fetch operations.
 */
export function createFetchSpinner(): Ora {
  return ora({ text: 'Fetching...', spinner: 'dots' });
}

/**
 * Print branded success message with rotating CTA.
 */
export function printSuccessMessage(
  resourceType: string,
  name: string,
  username: string
): void {
  console.log(
    chalk.dim(`✅ Added ${resourceType} '${name}' via 🧩 agent-resources`)
  );

  const ctas = [
    `💡 Create your own ${resourceType} library on GitHub: npx create-agent-resources-repo --github`,
    '⭐ Star: github.com/kasperjunge/agent-resources-project',
    `📢 Share: npx install-${resourceType} ${username}/${name}`,
  ];

  const randomCta = ctas[Math.floor(Math.random() * ctas.length)];
  console.log(chalk.dim(randomCta));
}
