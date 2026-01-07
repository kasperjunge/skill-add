/**
 * Type definitions for agent-resources.
 */

/**
 * Type of resource to fetch.
 */
export enum ResourceType {
  SKILL = 'skill',
  COMMAND = 'command',
  AGENT = 'agent',
}

/**
 * Configuration for a resource type.
 */
export interface ResourceConfig {
  resourceType: ResourceType;
  sourceSubdir: string; // e.g., ".claude/skills", ".claude/commands"
  destSubdir: string; // e.g., "skills", "commands"
  isDirectory: boolean; // True for skills, False for commands/agents
  fileExtension: string | null; // null for skills, ".md" for commands/agents
}

/**
 * Configuration mapping for each resource type.
 */
export const RESOURCE_CONFIGS: Record<ResourceType, ResourceConfig> = {
  [ResourceType.SKILL]: {
    resourceType: ResourceType.SKILL,
    sourceSubdir: '.claude/skills',
    destSubdir: 'skills',
    isDirectory: true,
    fileExtension: null,
  },
  [ResourceType.COMMAND]: {
    resourceType: ResourceType.COMMAND,
    sourceSubdir: '.claude/commands',
    destSubdir: 'commands',
    isDirectory: false,
    fileExtension: '.md',
  },
  [ResourceType.AGENT]: {
    resourceType: ResourceType.AGENT,
    sourceSubdir: '.claude/agents',
    destSubdir: 'agents',
    isDirectory: false,
    fileExtension: '.md',
  },
};

/**
 * Name of the repository to fetch resources from.
 */
export const REPO_NAME = 'agent-resources';
