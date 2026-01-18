# Troubleshooting

## Repository not found

**Error**: Repository does not exist or is inaccessible.

**Causes**:
- Typo in username or repo name
- Repository is private
- Default branch is not `main`

**Solutions**:
1. Verify the username and repo name are correct
2. Ensure the repository is public
3. Check that the default branch is `main`

---

## Resource not found

**Error**: Resource does not exist in the repository.

**Causes**:
- Resource path doesn't match expected structure
- Typo in resource name
- Nested path not formatted correctly

**Solutions**:
1. Verify the resource exists at the expected path:
   - Skills: `.claude/skills/<name>/SKILL.md`
   - Commands: `.claude/commands/<name>.md`
   - Agents: `.claude/agents/<name>.md`
2. For nested paths, verify folder structure matches `:` segments
3. Use `--type` if the resource exists in a non-standard location

---

## Resource already exists

**Error**: Destination already exists.

**Solution**: Use `--overwrite` to replace:
```bash
agr add username/my-skill --overwrite
```

---

## Ambiguous resource type

**Error**: Resource 'hello' found in multiple types: skill, command.

**Cause**: Same name exists as both a skill and command (or other types).

**Solution**: Use `--type` to specify which one:
```bash
agr add username/hello --type skill
agr add username/hello --type command
```

Works for `agr add`, `agr remove`, and `agrx`.

---

## agr.toml not found

**Error**: No agr.toml found when running `agr sync`.

**Solutions**:
1. Run `agr add` to create one automatically
2. Or create manually:
```toml
[dependencies]
"username/my-resource" = {}
```

---

## Sync not installing resources

**Symptom**: `agr sync` skips resources that should be installed.

**Causes**:
- Resources not listed in `agr.toml`
- Reference format is incorrect
- Resources already installed (expected behavior)

**Solutions**:
1. Verify resources are listed in `agr.toml`
2. Check reference format: `username/name` or `username/repo/name`
3. Already-installed resources are skipped intentionally

---

## Prune not removing resources

**Symptom**: `agr sync --prune` doesn't remove some resources.

**Cause**: Pruning only affects namespaced paths.

**Details**:
- Pruned: `.claude/skills/username/resource/`
- Preserved: `.claude/skills/resource/` (flat paths from older versions)

This preserves backward compatibility with older installations.

**Solution**: Manually remove flat-path resources if needed:
```bash
rm -rf .claude/skills/old-resource/
```

---

## Username shows as "local"

**Symptom**: Resources install to `.claude/skills/local/` instead of your username.

**Cause**: No git remote configured.

**Solution**: Add a git remote:
```bash
git remote add origin git@github.com:your-username/your-repo.git
agr sync --prune  # Re-sync with correct username
```

---

## Network errors

**Symptom**: Download fails or times out.

**Cause**: Network connectivity issues.

**Solutions**:
1. Check internet connection
2. Verify GitHub is accessible
3. Try again

---

## Permission denied

**Symptom**: Cannot write to `.claude/` directory.

**Solutions**:
1. Check directory permissions
2. For global installs, verify `~/.claude/` is writable
3. Run with appropriate permissions

---

## Deprecated syntax warning

**Symptom**: Warning about deprecated command syntax.

**Cause**: Using old subcommand syntax.

**Solution**: Update to new syntax:
```bash
# Old (deprecated)
agr add skill username/name
agr remove skill name

# New
agr add username/name
agr remove name
```

Type is auto-detected. Use `--type` only when disambiguation is needed.
