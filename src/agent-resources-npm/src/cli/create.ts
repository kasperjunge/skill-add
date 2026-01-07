/**
 * CLI for create-agent-resources-repo command.
 */

import * as path from 'node:path';
import * as fs from 'fs-extra';
import { Command } from 'commander';
import {
  checkGhCli,
  createGithubRepo,
  getGithubUsername,
  repoExists,
} from '../github.js';
import { createAgentResourcesRepo, initGit } from '../scaffold.js';

/**
 * Create the create-agent-resources-repo CLI command.
 */
export function createCreateCommand(): Command {
  const program = new Command()
    .name('create-agent-resources-repo')
    .description('Create a personal agent-resources repository.')
    .option(
      '-p, --path <path>',
      'Directory to create (default: ./agent-resources)'
    )
    .option(
      '-g, --github',
      'Create GitHub repository and push (requires gh CLI)',
      false
    )
    .action(async (options: { path?: string; github: boolean }) => {
      // Determine output path
      const outputPath =
        options.path || path.join(process.cwd(), 'agent-resources');

      // Check if directory already exists
      if (await fs.pathExists(outputPath)) {
        console.error(`Error: Directory already exists: ${outputPath}`);
        process.exit(1);
      }

      // Get username for README (if GitHub integration enabled)
      let username = '<username>';
      if (options.github) {
        if (!checkGhCli()) {
          console.error(
            'Error: GitHub CLI (gh) is not installed or not authenticated.'
          );
          console.error('Install: https://cli.github.com/');
          console.error('Then run: gh auth login');
          process.exit(1);
        }

        // Check if repo already exists on GitHub
        if (repoExists()) {
          console.error(
            "Error: Repository 'agent-resources' already exists on GitHub."
          );
          console.error('Delete it first or use a different approach.');
          process.exit(1);
        }

        username = getGithubUsername() || '<username>';
      }

      // Create the repository structure
      console.log(`Creating agent-resources repository at ${outputPath}...`);
      await createAgentResourcesRepo(outputPath, username);
      console.log('  Created directory structure');
      console.log('  Added hello-world skill');
      console.log('  Added hello command');
      console.log('  Added hello-agent agent');
      console.log('  Created README.md');

      // Initialize git
      if (initGit(outputPath)) {
        console.log('  Initialized git repository');
      } else {
        console.error('  Warning: Could not initialize git repository');
      }

      // GitHub integration
      if (options.github) {
        console.log('Creating GitHub repository...');
        const repoUrl = createGithubRepo(outputPath);
        if (repoUrl) {
          console.log(`  Pushed to ${repoUrl}`);
          console.log('');
          console.log('Your agent-resources repo is ready!');
          console.log('Others can now install your resources:');
          console.log(`  npx install-skill ${username}/hello-world`);
          console.log(`  npx install-command ${username}/hello`);
          console.log(`  npx install-agent ${username}/hello-agent`);
        } else {
          console.error('  Error: Could not create GitHub repository');
          process.exit(1);
        }
      } else {
        console.log('');
        console.log('Next steps:');
        console.log("  1. Create a GitHub repository named 'agent-resources'");
        console.log(`  2. cd ${outputPath}`);
        console.log('  3. git remote add origin <your-repo-url>');
        console.log('  4. git push -u origin main');
        console.log('');
        console.log('Or use --github flag to automate this (requires gh CLI)');
      }
    });

  return program;
}
