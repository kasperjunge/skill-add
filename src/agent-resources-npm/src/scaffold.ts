/**
 * Scaffolding functions for creating agent-resources repository structure.
 */

import { writeFile } from 'node:fs/promises';
import * as fs from 'fs-extra';
import * as path from 'node:path';
import { spawnSync } from 'node:child_process';

const HELLO_SKILL = `\
---
name: hello-world
description: A simple example skill that demonstrates Claude Code skill structure
---

# Hello World Skill

This is a demonstration skill showing how skills work.

## When to Use

Apply this skill when the user asks you to say hello or demonstrate skills.

## Instructions

Respond with a friendly greeting explaining this came from a skill.
`;

const HELLO_COMMAND = `\
---
description: Say hello - example slash command
---

When the user runs /hello, respond with a friendly greeting.
Explain that this is an example command from their agent-resources repo.
`;

const HELLO_AGENT = `\
---
description: Example subagent that greets users
---

You are a friendly greeter subagent.
When invoked, introduce yourself and explain that you're an example agent
from the user's agent-resources repository.
`;

const README_TEMPLATE = `\
# agent-resources

My personal collection of Claude Code skills, commands, and agents.

## Structure

\`\`\`
.claude/
├── skills/       # Skill directories with SKILL.md
├── commands/     # Slash command .md files
└── agents/       # Subagent .md files
\`\`\`

## Usage

Others can install my resources using:

\`\`\`bash
# Install a skill
npx install-skill {username}/hello-world

# Install a command
npx install-command {username}/hello

# Install an agent
npx install-agent {username}/hello-agent
\`\`\`

## Adding Resources

- **Skills**: Create a directory in \`.claude/skills/<name>/\` with a \`SKILL.md\` file
- **Commands**: Create a \`.md\` file in \`.claude/commands/\`
- **Agents**: Create a \`.md\` file in \`.claude/agents/\`

## Learn More

- [agent-resources documentation](https://github.com/kasperjunge/agent-resources-project)
`;

const GITIGNORE = `\
# Node
node_modules/
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
venv/

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/
*.swp
*.swo
`;

/**
 * Create the complete agent-resources directory structure.
 */
export async function scaffoldRepo(repoPath: string): Promise<void> {
  await fs.ensureDir(repoPath);

  // Create .claude directory structure
  const claudeDir = path.join(repoPath, '.claude');
  await fs.ensureDir(path.join(claudeDir, 'skills', 'hello-world'));
  await fs.ensureDir(path.join(claudeDir, 'commands'));
  await fs.ensureDir(path.join(claudeDir, 'agents'));
}

/**
 * Write the hello-world example skill.
 */
export async function writeStarterSkill(repoPath: string): Promise<void> {
  const skillPath = path.join(
    repoPath,
    '.claude',
    'skills',
    'hello-world',
    'SKILL.md'
  );
  await writeFile(skillPath, HELLO_SKILL, 'utf8');
}

/**
 * Write the hello example command.
 */
export async function writeStarterCommand(repoPath: string): Promise<void> {
  const commandPath = path.join(repoPath, '.claude', 'commands', 'hello.md');
  await writeFile(commandPath, HELLO_COMMAND, 'utf8');
}

/**
 * Write the hello-agent example agent.
 */
export async function writeStarterAgent(repoPath: string): Promise<void> {
  const agentPath = path.join(repoPath, '.claude', 'agents', 'hello-agent.md');
  await writeFile(agentPath, HELLO_AGENT, 'utf8');
}

/**
 * Write the README.md file.
 */
export async function writeReadme(
  repoPath: string,
  username: string = '<username>'
): Promise<void> {
  const readmePath = path.join(repoPath, 'README.md');
  await writeFile(
    readmePath,
    README_TEMPLATE.replace(/{username}/g, username),
    'utf8'
  );
}

/**
 * Write the .gitignore file.
 */
export async function writeGitignore(repoPath: string): Promise<void> {
  const gitignorePath = path.join(repoPath, '.gitignore');
  await writeFile(gitignorePath, GITIGNORE, 'utf8');
}

/**
 * Initialize git repository and create initial commit.
 *
 * @returns True if successful, false otherwise.
 */
export function initGit(repoPath: string): boolean {
  try {
    let result = spawnSync('git', ['init'], {
      cwd: repoPath,
      encoding: 'utf8',
      stdio: 'pipe',
    });
    if (result.status !== 0) return false;

    result = spawnSync('git', ['add', '.'], {
      cwd: repoPath,
      encoding: 'utf8',
      stdio: 'pipe',
    });
    if (result.status !== 0) return false;

    result = spawnSync(
      'git',
      ['commit', '-m', 'Initial commit: agent-resources repo scaffold'],
      {
        cwd: repoPath,
        encoding: 'utf8',
        stdio: 'pipe',
      }
    );
    if (result.status !== 0) return false;

    return true;
  } catch {
    return false;
  }
}

/**
 * Create a complete agent-resources repository with all starter content.
 */
export async function createAgentResourcesRepo(
  repoPath: string,
  username: string = '<username>'
): Promise<void> {
  await scaffoldRepo(repoPath);
  await writeStarterSkill(repoPath);
  await writeStarterCommand(repoPath);
  await writeStarterAgent(repoPath);
  await writeReadme(repoPath, username);
  await writeGitignore(repoPath);
}
