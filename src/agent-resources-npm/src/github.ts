/**
 * GitHub CLI integration for creating and pushing repositories.
 */

import { spawnSync } from 'node:child_process';

/**
 * Check if GitHub CLI is available and authenticated.
 *
 * @returns True if gh CLI is installed and authenticated, false otherwise.
 */
export function checkGhCli(): boolean {
  try {
    const result = spawnSync('gh', ['auth', 'status'], {
      encoding: 'utf8',
      stdio: 'pipe',
    });
    return result.status === 0;
  } catch {
    return false;
  }
}

/**
 * Get the authenticated GitHub username.
 *
 * @returns The username if authenticated, null otherwise.
 */
export function getGithubUsername(): string | null {
  try {
    const result = spawnSync('gh', ['api', 'user', '--jq', '.login'], {
      encoding: 'utf8',
      stdio: 'pipe',
    });
    if (result.status === 0 && result.stdout) {
      return result.stdout.trim();
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Create a GitHub repository and push the local repo.
 *
 * @param repoPath - Path to the local git repository
 * @param repoName - Name for the GitHub repository (default: agent-resources)
 * @returns The GitHub repo URL if successful, null otherwise.
 */
export function createGithubRepo(
  repoPath: string,
  repoName: string = 'agent-resources'
): string | null {
  try {
    // Create repo on GitHub (public by default)
    const result = spawnSync(
      'gh',
      ['repo', 'create', repoName, '--public', '--source', repoPath, '--push'],
      {
        encoding: 'utf8',
        stdio: 'pipe',
      }
    );

    if (result.status !== 0) {
      return null;
    }

    // Extract URL from output or construct it
    const username = getGithubUsername();
    if (username) {
      return `https://github.com/${username}/${repoName}`;
    }

    return null;
  } catch {
    return null;
  }
}

/**
 * Check if a repository with the given name already exists.
 *
 * @returns True if the repo exists, false otherwise.
 */
export function repoExists(repoName: string = 'agent-resources'): boolean {
  try {
    const result = spawnSync('gh', ['repo', 'view', repoName], {
      encoding: 'utf8',
      stdio: 'pipe',
    });
    return result.status === 0;
  } catch {
    return false;
  }
}
