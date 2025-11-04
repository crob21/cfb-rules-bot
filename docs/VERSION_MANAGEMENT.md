# Version Management Guide 📜

This guide explains how to manage versions and maintain the changelog for the CFB Rules Bot (Harry).

## Overview

The bot uses **Semantic Versioning** (SemVer) to track releases and changes.

**Current Version:** 1.1.0
**Version File:** `src/cfb_bot/utils/version_manager.py`

---

## Semantic Versioning (SemVer)

Version format: `MAJOR.MINOR.PATCH`

### MAJOR Version (X.0.0)
Increment when you make **incompatible API changes** or **major redesigns**

**Examples:**
- Complete bot rewrite
- Breaking changes to command syntax
- Major architecture changes
- Removing features

### MINOR Version (1.X.0)
Increment when you add **new features** in a backwards-compatible manner

**Examples:**
- Adding new slash commands
- Adding new features (like advance timer, summarization)
- New integrations
- Significant improvements

### PATCH Version (1.1.X)
Increment when you make **backwards-compatible bug fixes**

**Examples:**
- Bug fixes
- Performance improvements
- Small tweaks
- Documentation updates
- Minor text changes

---

## How to Update Version

### Step 1: Determine Version Increment

Ask yourself:
- **Did I add new features?** → Increment MINOR (1.1.0 → 1.2.0)
- **Did I just fix bugs?** → Increment PATCH (1.1.0 → 1.1.1)
- **Did I make breaking changes?** → Increment MAJOR (1.1.0 → 2.0.0)

### Step 2: Edit version_manager.py

Open `src/cfb_bot/utils/version_manager.py`

#### Update CURRENT_VERSION

```python
# Change this line:
CURRENT_VERSION = "1.1.0"

# To new version:
CURRENT_VERSION = "1.2.0"
```

#### Add Changelog Entry

Add a new entry to the `CHANGELOG` dictionary:

```python
CHANGELOG: Dict[str, Dict] = {
    "1.2.0": {  # NEW VERSION HERE
        "date": "2025-11-15",  # Release date
        "title": "Brief Description",  # Short title
        "emoji": "🚀",  # Emoji for this release
        "features": [
            {
                "category": "Feature Category",
                "emoji": "⚡",
                "changes": [
                    "First change description",
                    "Second change description",
                    "Third change description"
                ]
            },
            # Add more feature categories as needed
        ]
    },
    "1.1.0": {  # Keep existing versions below
        # ... existing changelog
    }
}
```

### Step 3: Write Good Changelog Entries

**Good changelog entries are:**
- ✅ Clear and concise
- ✅ User-focused (what users can do)
- ✅ Specific about what changed
- ✅ Action-oriented

**Examples:**

✅ **Good:**
- "Added `/advance` command with custom duration support"
- "Channel summarization now supports focus keywords"
- "Fixed countdown timer not sending 1-hour notification"

❌ **Bad:**
- "Updated code"
- "Fixed stuff"
- "Made changes to bot.py"

### Step 4: Commit and Push

```bash
git add src/cfb_bot/utils/version_manager.py
git commit -m "Bump version to 1.2.0"
git push
```

Then commit your actual changes:

```bash
git add .
git commit -m "Add [feature name] - v1.2.0

- Feature 1 description
- Feature 2 description
- Feature 3 description"
git push
```

---

## Changelog Structure

### Full Example

```python
"1.2.0": {
    "date": "2025-11-15",
    "title": "Advanced Notifications",
    "emoji": "🔔",
    "features": [
        {
            "category": "Notifications",
            "emoji": "🔔",
            "changes": [
                "Added custom notification intervals",
                "Email notifications for countdown end",
                "DM notifications for important events"
            ]
        },
        {
            "category": "Bug Fixes",
            "emoji": "🐛",
            "changes": [
                "Fixed timer not persisting after restart",
                "Fixed progress bar calculation error",
                "Improved error handling"
            ]
        }
    ]
}
```

### Category Examples

Common categories to use:
- **Core Features** - Main functionality
- **Commands** - New or updated commands
- **Notifications** - Notification system changes
- **Bug Fixes** - Bug fixes and corrections
- **Performance** - Performance improvements
- **UI/UX** - User interface improvements
- **Admin Tools** - Admin-only features
- **Integration** - Third-party integrations
- **Security** - Security improvements

---

## Testing Your Changes

Before deploying:

1. **Check version displays correctly:**
   - Run bot locally
   - Check startup logs for version number
   - Test `/version` command
   - Test `/changelog` command
   - Test `/changelog [your-new-version]`

2. **Verify changelog formatting:**
   - Check embeds display properly
   - Verify all features are listed
   - Ensure emoji show correctly

3. **Test new features:**
   - Verify all new commands work
   - Check error handling
   - Test edge cases

---

## Version History Reference

### Current Versions

| Version | Date | Title | Major Changes |
|---------|------|-------|---------------|
| 1.1.0 | 2025-11-04 | Major Feature Update | Advance timer, summarization, charter management, bot admins, version control |
| 1.0.0 | 2025-10-15 | Initial Release | Core bot, AI integration, basic commands |

### Planned Versions

| Version | Expected | Planned Features |
|---------|----------|------------------|
| 1.2.0 | TBD | Persistent timers, enhanced summarization |
| 2.0.0 | TBD | Major architecture update |

---

## Quick Reference Checklist

When releasing a new version:

- [ ] Determine correct version number (MAJOR.MINOR.PATCH)
- [ ] Update `CURRENT_VERSION` in `version_manager.py`
- [ ] Add complete changelog entry with:
  - [ ] Correct version number
  - [ ] Release date
  - [ ] Descriptive title
  - [ ] Appropriate emoji
  - [ ] All features categorized
  - [ ] Clear change descriptions
- [ ] Test version commands locally
- [ ] Commit version update separately
- [ ] Commit feature changes with version reference
- [ ] Push to repository
- [ ] Verify deployment
- [ ] Test in production
- [ ] Announce to users with `/whats_new`

---

## Common Mistakes to Avoid

❌ **Forgetting to update version** - Always update when adding features!

❌ **Vague changelog entries** - Be specific about what changed

❌ **Wrong version increment** - Follow SemVer rules

❌ **Missing date** - Always include release date

❌ **Not testing** - Test `/version` and `/changelog` before deploying

❌ **Inconsistent formatting** - Follow the established pattern

---

## Need Help?

If you're unsure about version numbering:

1. **Small fixes/tweaks?** → PATCH (1.1.0 → 1.1.1)
2. **New features/commands?** → MINOR (1.1.0 → 1.2.0)
3. **Breaking changes?** → MAJOR (1.1.0 → 2.0.0)

**When in doubt, increment MINOR for any user-facing changes!**

---

## Future Improvements

Consider adding:
- Automated version bumping scripts
- Changelog generation from git commits
- Release notes automation
- Version comparison tools

---

**Document Version:** 1.0
**Last Updated:** November 4, 2025
**Maintained By:** CFB Rules Bot Team
