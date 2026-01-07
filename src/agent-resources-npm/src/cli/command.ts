/**
 * CLI for add-command command.
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
 * Create the add-command CLI command.
 */
export function createCommandCommand(): Command {
  const program = new Command()
    .name('add-command')
    .description('Add Claude Code commands from GitHub to your project.')
    .argument(
      '<command-ref>',
      'Command to add in format: <username>/<command-name>'
    )
    .option('--overwrite', 'Overwrite existing command if it exists.', false)
    .option(
      '-g, --global',
      'Install to ~/.claude/ instead of ./.claude/',
      false
    )
    .action(
      async (
        commandRef: string,
        options: { overwrite: boolean; global: boolean }
      ) => {
        try {
          const [username, commandName] = parseResourceRef(commandRef);
          const dest = getDestination('commands', options.global);

          const spinner = createFetchSpinner();
          spinner.start();

          try {
            await fetchResource(
              username,
              commandName,
              dest,
              ResourceType.COMMAND,
              options.overwrite
            );
            spinner.stop();
            printSuccessMessage('command', commandName, username);
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
