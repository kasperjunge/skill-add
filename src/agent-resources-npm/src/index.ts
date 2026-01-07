/**
 * agent-resources - CLI tools for installing Claude Code resources from GitHub.
 */

// Types
export { ResourceType, RESOURCE_CONFIGS, REPO_NAME } from './types.js';
export type { ResourceConfig } from './types.js';

// Exceptions
export {
  ClaudeAddError,
  RepoNotFoundError,
  ResourceNotFoundError,
  ResourceExistsError,
} from './exceptions.js';

// Core functionality
export { fetchResource } from './fetcher.js';

// GitHub integration
export {
  checkGhCli,
  getGithubUsername,
  createGithubRepo,
  repoExists,
} from './github.js';

// Scaffolding
export {
  scaffoldRepo,
  writeStarterSkill,
  writeStarterCommand,
  writeStarterAgent,
  writeReadme,
  writeGitignore,
  initGit,
  createAgentResourcesRepo,
} from './scaffold.js';

// CLI utilities
export {
  parseResourceRef,
  getDestination,
  createFetchSpinner,
  printSuccessMessage,
} from './cli/common.js';

// CLI commands
export { createSkillCommand } from './cli/skill.js';
export { createCommandCommand } from './cli/command.js';
export { createAgentCommand } from './cli/agent.js';
export { createCreateCommand } from './cli/create.js';
