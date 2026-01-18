# /docs - Document Feature Branch Changes

Update project documentation to reflect work completed on the current feature branch.

## Instructions

1. **Analyze the current branch**
   - Run `git diff main...HEAD --stat` to identify all changed files
   - Run `git log main..HEAD --oneline` to understand commit history
   - Read the modified/added source files to understand the feature

2. **Identify documentation scope**
   - What new functionality was added?
   - What existing behavior changed?
   - Are there new CLI commands, API endpoints, or configuration options?
   - Are there breaking changes users need to know about?

3. **Update README.md**
   - Add/update feature descriptions in the appropriate section
   - Include usage examples with realistic inputs/outputs
   - Document any new installation steps or dependencies
   - Keep it concise—README is for quick orientation

4. **Update MkDocs documentation** (in `docs/` directory)
   - Create or update relevant pages for detailed documentation
   - Include complete API/CLI reference for new features
   - Add configuration options with defaults and examples
   - Update `mkdocs.yml` nav if adding new pages
   - Cross-link related documentation pages

5. **Documentation standards**
   - Write for users who haven't seen the code
   - Lead with the "why" before the "how"
   - Include copy-pasteable examples
   - Document error cases and troubleshooting
   - Use consistent terminology with existing docs

## Output

Summarize what documentation was added or changed when complete.
