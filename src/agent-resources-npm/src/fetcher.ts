/**
 * Generic resource fetcher for skills, commands, and agents.
 */

import { createWriteStream } from 'node:fs';
import { mkdtemp } from 'node:fs/promises';
import * as fs from 'fs-extra';
import * as os from 'node:os';
import * as path from 'node:path';
import { pipeline } from 'node:stream/promises';
import { Readable } from 'node:stream';
import * as tar from 'tar';

import {
  ClaudeAddError,
  RepoNotFoundError,
  ResourceExistsError,
  ResourceNotFoundError,
} from './exceptions.js';
import { ResourceType, RESOURCE_CONFIGS, REPO_NAME } from './types.js';

/**
 * Capitalize the first letter of a string.
 */
function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Fetch a resource from a user's agent-resources repo and copy it to dest.
 *
 * @param username - GitHub username
 * @param name - Name of the resource to fetch
 * @param dest - Destination directory (e.g., .claude/skills/, .claude/commands/)
 * @param resourceType - Type of resource (SKILL, COMMAND, or AGENT)
 * @param overwrite - Whether to overwrite existing resource
 * @returns Path to the installed resource
 * @throws RepoNotFoundError - If the agent-resources repo doesn't exist
 * @throws ResourceNotFoundError - If the resource doesn't exist in the repo
 * @throws ResourceExistsError - If resource exists locally and overwrite=false
 */
export async function fetchResource(
  username: string,
  name: string,
  dest: string,
  resourceType: ResourceType,
  overwrite: boolean = false
): Promise<string> {
  const config = RESOURCE_CONFIGS[resourceType];

  // Determine destination path
  let resourceDest: string;
  if (config.isDirectory) {
    resourceDest = path.join(dest, name);
  } else {
    resourceDest = path.join(dest, `${name}${config.fileExtension}`);
  }

  // Check if resource already exists locally
  if ((await fs.pathExists(resourceDest)) && !overwrite) {
    throw new ResourceExistsError(
      `${capitalize(resourceType)} '${name}' already exists at ${resourceDest}\n` +
        `Use --overwrite to replace it.`
    );
  }

  // Download tarball
  const tarballUrl = `https://github.com/${username}/${REPO_NAME}/archive/refs/heads/main.tar.gz`;
  const tmpDir = await mkdtemp(path.join(os.tmpdir(), 'agent-resources-'));

  try {
    const tarballPath = path.join(tmpDir, 'repo.tar.gz');

    // Download
    let response: Response;
    try {
      response = await fetch(tarballUrl, { redirect: 'follow' });
    } catch (error) {
      throw new ClaudeAddError(`Network error: ${error}`);
    }

    if (response.status === 404) {
      throw new RepoNotFoundError(
        `Repository '${username}/${REPO_NAME}' not found on GitHub.`
      );
    }

    if (!response.ok) {
      throw new ClaudeAddError(
        `Failed to download repository: HTTP ${response.status}`
      );
    }

    // Write to file
    const body = response.body;
    if (!body) {
      throw new ClaudeAddError('Empty response body');
    }

    await pipeline(
      Readable.fromWeb(body as Parameters<typeof Readable.fromWeb>[0]),
      createWriteStream(tarballPath)
    );

    // Extract
    const extractPath = path.join(tmpDir, 'extracted');
    await fs.ensureDir(extractPath);
    await tar.extract({ file: tarballPath, cwd: extractPath });

    // Find the resource in extracted content
    // Tarball extracts to: agent-resources-main/.claude/<type>/<name>[.md]
    const repoDir = path.join(extractPath, `${REPO_NAME}-main`);

    let resourceSource: string;
    if (config.isDirectory) {
      resourceSource = path.join(repoDir, config.sourceSubdir, name);
    } else {
      resourceSource = path.join(
        repoDir,
        config.sourceSubdir,
        `${name}${config.fileExtension}`
      );
    }

    if (!(await fs.pathExists(resourceSource))) {
      let expectedLocation: string;
      if (config.isDirectory) {
        expectedLocation = `${config.sourceSubdir}/${name}/`;
      } else {
        expectedLocation = `${config.sourceSubdir}/${name}${config.fileExtension}`;
      }
      throw new ResourceNotFoundError(
        `${capitalize(resourceType)} '${name}' not found in ${username}/${REPO_NAME}.\n` +
          `Expected location: ${expectedLocation}`
      );
    }

    // Remove existing if overwriting
    if (await fs.pathExists(resourceDest)) {
      await fs.remove(resourceDest);
    }

    // Ensure destination parent exists
    await fs.ensureDir(dest);

    // Copy resource to destination
    await fs.copy(resourceSource, resourceDest);

    return resourceDest;
  } finally {
    // Cleanup temp directory
    await fs.remove(tmpDir);
  }
}
