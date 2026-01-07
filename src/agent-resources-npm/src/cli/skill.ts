/**
 * CLI for add-skill command.
 */

import { Command } from 'commander';
import {
  parseResourceRef,
  getDestination,
  createFetchSpinner,
  printSuccessMessage,
} from './common.js';
import { fetchResource } from '../fetcher.js';
import { ResourceType } from '../types.js';
import {
  ClaudeAddError,
  RepoNotFoundError,
  ResourceExistsError,
  ResourceNotFoundError,
} from '../exceptions.js';

/**
 * Create the add-skill CLI command.
 */
export function createSkillCommand(): Command {
  const program = new Command()
    .name('add-skill')
    .description('Add Claude Code skills from GitHub to your project.')
    .argument(
      '<skill-ref>',
      'Skill to add in format: <username>/<skill-name>'
    )
    .option('--overwrite', 'Overwrite existing skill if it exists.', false)
    .option(
      '-g, --global',
      'Install to ~/.claude/ instead of ./.claude/',
      false
    )
    .action(
      async (
        skillRef: string,
        options: { overwrite: boolean; global: boolean }
      ) => {
        try {
          const [username, skillName] = parseResourceRef(skillRef);
          const dest = getDestination('skills', options.global);

          const spinner = createFetchSpinner();
          spinner.start();

          try {
            await fetchResource(
              username,
              skillName,
              dest,
              ResourceType.SKILL,
              options.overwrite
            );
            spinner.stop();
            printSuccessMessage('skill', skillName, username);
          } catch (error) {
            spinner.stop();
            throw error;
          }
        } catch (error) {
          if (
            error instanceof RepoNotFoundError ||
            error instanceof ResourceNotFoundError ||
            error instanceof ResourceExistsError ||
            error instanceof ClaudeAddError
          ) {
            console.error(`Error: ${error.message}`);
            process.exit(1);
          }
          if (error instanceof Error) {
            console.error(`Error: ${error.message}`);
            process.exit(1);
          }
          throw error;
        }
      }
    );

  return program;
}
