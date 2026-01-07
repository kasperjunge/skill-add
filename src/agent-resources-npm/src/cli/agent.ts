/**
 * CLI for add-agent command.
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
 * Create the add-agent CLI command.
 */
export function createAgentCommand(): Command {
  const program = new Command()
    .name('add-agent')
    .description('Add Claude Code agents from GitHub to your project.')
    .argument(
      '<agent-ref>',
      'Agent to add in format: <username>/<agent-name>'
    )
    .option('--overwrite', 'Overwrite existing agent if it exists.', false)
    .option(
      '-g, --global',
      'Install to ~/.claude/ instead of ./.claude/',
      false
    )
    .action(
      async (
        agentRef: string,
        options: { overwrite: boolean; global: boolean }
      ) => {
        try {
          const [username, agentName] = parseResourceRef(agentRef);
          const dest = getDestination('agents', options.global);

          const spinner = createFetchSpinner();
          spinner.start();

          try {
            await fetchResource(
              username,
              agentName,
              dest,
              ResourceType.AGENT,
              options.overwrite
            );
            spinner.stop();
            printSuccessMessage('agent', agentName, username);
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
