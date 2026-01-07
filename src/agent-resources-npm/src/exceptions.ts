/**
 * Shared exception classes for agent-resources.
 */

/**
 * Base exception for claude-add errors.
 */
export class ClaudeAddError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ClaudeAddError';
    Object.setPrototypeOf(this, ClaudeAddError.prototype);
  }
}

/**
 * Raised when the agent-resources repo doesn't exist.
 */
export class RepoNotFoundError extends ClaudeAddError {
  constructor(message: string) {
    super(message);
    this.name = 'RepoNotFoundError';
    Object.setPrototypeOf(this, RepoNotFoundError.prototype);
  }
}

/**
 * Raised when the skill/command/agent doesn't exist in the repo.
 */
export class ResourceNotFoundError extends ClaudeAddError {
  constructor(message: string) {
    super(message);
    this.name = 'ResourceNotFoundError';
    Object.setPrototypeOf(this, ResourceNotFoundError.prototype);
  }
}

/**
 * Raised when the resource already exists locally.
 */
export class ResourceExistsError extends ClaudeAddError {
  constructor(message: string) {
    super(message);
    this.name = 'ResourceExistsError';
    Object.setPrototypeOf(this, ResourceExistsError.prototype);
  }
}
