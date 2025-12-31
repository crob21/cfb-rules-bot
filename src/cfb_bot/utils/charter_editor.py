#!/usr/bin/env python3
"""
Charter Editor Module for CFB 26 League Bot
Handles editing and updating the league charter with interactive AI updates
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger('CFB26Bot.CharterEditor')

class CharterEditor:
    """Handles editing and updating the league charter"""

    def __init__(self, ai_assistant=None):
        self.ai_assistant = ai_assistant
        self.charter_file = "data/charter_content.txt"
        self.backup_dir = "data/charter_backups"

        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)

    def read_charter(self) -> Optional[str]:
        """Read the current charter content"""
        try:
            if os.path.exists(self.charter_file):
                with open(self.charter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"📄 Read charter: {len(content)} characters")
                return content
            else:
                logger.warning("⚠️ Charter file not found")
                return None
        except Exception as e:
            logger.error(f"❌ Error reading charter: {e}")
            return None

    def backup_charter(self) -> bool:
        """Create a backup of the current charter"""
        try:
            content = self.read_charter()
            if not content:
                return False

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f"charter_backup_{timestamp}.txt")

            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"💾 Charter backed up to {backup_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Error backing up charter: {e}")
            return False

    def write_charter(self, content: str) -> bool:
        """Write new content to the charter"""
        try:
            # First, create a backup
            self.backup_charter()

            # Write the new content
            with open(self.charter_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"✅ Charter updated: {len(content)} characters")
            return True
        except Exception as e:
            logger.error(f"❌ Error writing charter: {e}")
            return False

    async def add_rule_section(
        self,
        section_title: str,
        section_content: str,
        position: Optional[str] = None
    ) -> Dict:
        """
        Add a new rule section to the charter

        Args:
            section_title: Title of the new section
            section_content: Content of the new section
            position: Where to add it (e.g., "end", "after:1.7", "before:2.1")

        Returns:
            Dict with status and message
        """
        try:
            current_charter = self.read_charter()
            if not current_charter:
                return {
                    'success': False,
                    'message': 'Could not read current charter'
                }

            # Format the new section
            new_section = f"\n\n### {section_title}\n{section_content}\n"

            # Determine where to insert
            if not position or position == "end":
                # Add to the end
                updated_charter = current_charter + new_section
            elif position.startswith("after:"):
                # Add after a specific section
                target = position.split(":", 1)[1]
                # Find the target section and insert after it
                # This is a simple implementation - could be enhanced
                updated_charter = current_charter.replace(
                    f"### {target}",
                    f"### {target}{new_section}"
                )
            elif position.startswith("before:"):
                # Add before a specific section
                target = position.split(":", 1)[1]
                updated_charter = current_charter.replace(
                    f"### {target}",
                    f"{new_section}\n### {target}"
                )
            else:
                updated_charter = current_charter + new_section

            # Write the updated charter
            success = self.write_charter(updated_charter)

            if success:
                return {
                    'success': True,
                    'message': f'Successfully added section: {section_title}',
                    'new_content': new_section
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to write updated charter'
                }

        except Exception as e:
            logger.error(f"❌ Error adding rule section: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    async def update_rule_section(
        self,
        section_identifier: str,
        new_content: str
    ) -> Dict:
        """
        Update an existing rule section

        Args:
            section_identifier: Identifier for the section (e.g., "1.1", "Scheduling")
            new_content: New content for the section

        Returns:
            Dict with status and message
        """
        try:
            current_charter = self.read_charter()
            if not current_charter:
                return {
                    'success': False,
                    'message': 'Could not read current charter'
                }

            # Try to find and replace the section
            # This is a simple implementation - looks for section headers
            lines = current_charter.split('\n')
            updated_lines = []
            in_target_section = False
            section_found = False

            for i, line in enumerate(lines):
                # Check if this is our target section
                if section_identifier in line and (line.startswith('##') or line.startswith('###')):
                    in_target_section = True
                    section_found = True
                    updated_lines.append(line)  # Keep the header
                    updated_lines.append(new_content)  # Add new content
                    continue

                # If we're in the target section, skip until next section
                if in_target_section:
                    if line.startswith('##'):
                        # We've reached the next section
                        in_target_section = False
                        updated_lines.append(line)
                    # Skip old content while in target section
                    continue

                # Keep all other lines
                updated_lines.append(line)

            if not section_found:
                return {
                    'success': False,
                    'message': f'Section "{section_identifier}" not found in charter'
                }

            updated_charter = '\n'.join(updated_lines)
            success = self.write_charter(updated_charter)

            if success:
                return {
                    'success': True,
                    'message': f'Successfully updated section: {section_identifier}'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to write updated charter'
                }

        except Exception as e:
            logger.error(f"❌ Error updating rule section: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    async def format_rule_with_ai(
        self,
        rule_summary: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Use AI to format a rule summary into proper charter format

        Args:
            rule_summary: Summary of the rule to add
            context: Optional context (e.g., from channel summary)

        Returns:
            Formatted rule text
        """
        if not self.ai_assistant:
            # Return basic formatting without AI
            return f"**Rule**: {rule_summary}"

        try:
            context_text = f"\n\nContext: {context}" if context else ""

            prompt = f"""You are Harry, helping to format a new league rule for the CFB 26 League Charter.

Given this rule summary: {rule_summary}{context_text}

Format it as a proper charter rule entry. Use this style:
- Clear, concise language
- Professional tone (save the sarcasm for chat!)
- Bullet points for details if needed
- Include any relevant conditions or exceptions

Just provide the formatted rule text, nothing else."""

            logger.info(f"🤖 Requesting AI formatting for rule: {rule_summary[:50]}...")
            formatted_rule = await self.ai_assistant.ask_ai(prompt, "Charter Editor")

            if formatted_rule:
                logger.info("✅ AI rule formatting successful")
                return formatted_rule
            else:
                logger.warning("⚠️ AI formatting failed, using basic format")
                return f"**Rule**: {rule_summary}"

        except Exception as e:
            logger.error(f"❌ Error formatting rule with AI: {e}")
            return f"**Rule**: {rule_summary}"

    def update_commissioner(self, new_commish_name: str) -> Dict:
        """
        Update the league commissioner in the charter

        Args:
            new_commish_name: Name of the new commissioner

        Returns:
            Dict with status and message
        """
        try:
            current_charter = self.read_charter()
            if not current_charter:
                return {
                    'success': False,
                    'message': 'Could not read current charter'
                }

            lines = current_charter.split('\n')
            updated_lines = []
            commish_updated = False

            for line in lines:
                # Look for the League Commish line
                if '**League Commish:**' in line or 'League Commish:' in line:
                    # Extract the old name (if any) and replace with new one
                    updated_line = f"- **League Commish:** {new_commish_name}"
                    updated_lines.append(updated_line)
                    commish_updated = True
                    logger.info(f"📝 Updated commissioner: {new_commish_name}")
                else:
                    updated_lines.append(line)

            if not commish_updated:
                # If the section doesn't exist, try to add it after "## Officers"
                for i, line in enumerate(lines):
                    updated_lines.append(line)
                    if '## Officers' in line or 'Officers' in line:
                        # Add commissioner line after Officers header
                        updated_lines.append(f"- **League Commish:** {new_commish_name}")
                        commish_updated = True
                        break

            if commish_updated:
                updated_charter = '\n'.join(updated_lines)
                success = self.write_charter(updated_charter)

                if success:
                    return {
                        'success': True,
                        'message': f'Successfully updated League Commish to: {new_commish_name}'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Failed to write updated charter'
                    }
            else:
                return {
                    'success': False,
                    'message': 'Could not find Officers section in charter'
                }

        except Exception as e:
            logger.error(f"❌ Error updating commissioner: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    def get_backup_list(self) -> List[Dict]:
        """Get a list of available charter backups"""
        try:
            backups = []
            for filename in sorted(os.listdir(self.backup_dir), reverse=True):
                if filename.startswith("charter_backup_") and filename.endswith(".txt"):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)

                    # Extract timestamp from filename
                    timestamp_str = filename.replace("charter_backup_", "").replace(".txt", "")

                    backups.append({
                        'filename': filename,
                        'filepath': filepath,
                        'timestamp': timestamp_str,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })

            return backups
        except Exception as e:
            logger.error(f"❌ Error listing backups: {e}")
            return []

    def restore_backup(self, backup_filename: str) -> bool:
        """Restore a charter from backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)

            if not os.path.exists(backup_path):
                logger.error(f"❌ Backup file not found: {backup_filename}")
                return False

            # Read the backup
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()

            # Backup the current charter before restoring
            self.backup_charter()

            # Restore the backup
            success = self.write_charter(backup_content)

            if success:
                logger.info(f"✅ Charter restored from backup: {backup_filename}")

            return success

        except Exception as e:
            logger.error(f"❌ Error restoring backup: {e}")
            return False

    # ==================== Interactive Update Methods ====================

    def _load_changelog(self) -> List[Dict]:
        """Load the changelog from file"""
        changelog_file = "data/charter_changelog.json"
        try:
            if os.path.exists(changelog_file):
                with open(changelog_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"❌ Error loading changelog: {e}")
            return []

    def _save_changelog(self, changelog: List[Dict]) -> bool:
        """Save the changelog to file"""
        changelog_file = "data/charter_changelog.json"
        try:
            with open(changelog_file, 'w', encoding='utf-8') as f:
                json.dump(changelog, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"❌ Error saving changelog: {e}")
            return False

    def add_changelog_entry(
        self,
        user_id: int,
        user_name: str,
        action: str,
        description: str,
        before_text: Optional[str] = None,
        after_text: Optional[str] = None
    ) -> bool:
        """Add an entry to the changelog"""
        try:
            changelog = self._load_changelog()

            entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "user_name": user_name,
                "action": action,
                "description": description,
                "before": before_text[:500] if before_text else None,  # Limit size
                "after": after_text[:500] if after_text else None
            }

            changelog.append(entry)

            # Keep only last 100 entries
            if len(changelog) > 100:
                changelog = changelog[-100:]

            return self._save_changelog(changelog)
        except Exception as e:
            logger.error(f"❌ Error adding changelog entry: {e}")
            return False

    def get_recent_changes(self, limit: int = 10) -> List[Dict]:
        """Get recent changelog entries"""
        changelog = self._load_changelog()
        return changelog[-limit:][::-1]  # Most recent first

    async def parse_update_request(self, request: str) -> Optional[Dict]:
        """
        Use AI to parse a natural language update request

        Returns dict with:
        - action: 'update', 'add', 'remove', 'unknown'
        - section: which section to modify
        - old_text: text to find/replace (if updating)
        - new_text: new text to add
        - summary: human-readable summary of the change
        """
        if not self.ai_assistant:
            logger.warning("⚠️ AI assistant not available for parsing")
            return None

        current_charter = self.read_charter()
        if not current_charter:
            return None

        prompt = f"""You are helping to parse a charter update request for a CFB 26 league.

CURRENT CHARTER:
{current_charter}

UPDATE REQUEST: "{request}"

Analyze this request and determine:
1. What ACTION is being requested? (update/add/remove)
2. What SECTION is affected? (provide the section header or identifier)
3. What is the CURRENT TEXT that will be changed? (exact quote from charter, if updating)
4. What is the NEW TEXT? (the replacement or addition)
5. A brief SUMMARY of the change

Respond in this EXACT JSON format (no markdown, just raw JSON):
{{
    "action": "update|add|remove",
    "section": "section name or number",
    "old_text": "exact current text to replace (null if adding new)",
    "new_text": "the new or replacement text",
    "summary": "brief description of what's changing"
}}

If you cannot understand the request, respond with:
{{
    "action": "unknown",
    "error": "explanation of what's unclear"
}}"""

        try:
            response = await self.ai_assistant.ask_openai(prompt, "Charter Update Parser", max_tokens=1000)
            if not response:
                response = await self.ai_assistant.ask_anthropic(prompt, "Charter Update Parser", max_tokens=1000)

            if not response:
                return None

            # Clean up response - remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```\w*\n?', '', response)
                response = re.sub(r'\n?```$', '', response)

            # Parse JSON
            parsed = json.loads(response)
            logger.info(f"📝 Parsed update request: {parsed.get('action')} - {parsed.get('summary')}")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response as JSON: {e}")
            logger.error(f"Response was: {response}")
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing update request: {e}")
            return None

    async def generate_update_preview(self, parsed_request: Dict) -> Optional[Dict]:
        """
        Generate a before/after preview of the proposed change

        Returns dict with:
        - before: the text before the change
        - after: the text after the change
        - full_new_charter: the complete updated charter
        """
        current_charter = self.read_charter()
        if not current_charter:
            return None

        action = parsed_request.get("action")
        old_text = parsed_request.get("old_text")
        new_text = parsed_request.get("new_text")
        section = parsed_request.get("section")

        if action == "unknown":
            return None

        try:
            if action == "update" and old_text:
                # Find and replace
                if old_text in current_charter:
                    new_charter = current_charter.replace(old_text, new_text, 1)
                    return {
                        "before": old_text,
                        "after": new_text,
                        "full_new_charter": new_charter
                    }
                else:
                    # Try fuzzy matching - ask AI to find the right section
                    logger.warning(f"⚠️ Exact text not found, attempting fuzzy match")
                    return await self._fuzzy_update(current_charter, parsed_request)

            elif action == "add":
                # Add new content
                # Try to find the section to add to
                if section:
                    # Look for the section header
                    section_pattern = re.compile(
                        rf'(###?\s*{re.escape(section)}.*?)(\n##|\n###|\Z)',
                        re.IGNORECASE | re.DOTALL
                    )
                    match = section_pattern.search(current_charter)

                    if match:
                        section_content = match.group(1)
                        insert_pos = match.start() + len(section_content)
                        new_charter = (
                            current_charter[:insert_pos] +
                            f"\n\n{new_text}" +
                            current_charter[insert_pos:]
                        )
                        return {
                            "before": "(Adding new content)",
                            "after": new_text,
                            "full_new_charter": new_charter
                        }

                # Default: add at end
                new_charter = current_charter + f"\n\n{new_text}"
                return {
                    "before": "(Adding new content at end)",
                    "after": new_text,
                    "full_new_charter": new_charter
                }

            elif action == "remove" and old_text:
                # Remove content
                if old_text in current_charter:
                    new_charter = current_charter.replace(old_text, "", 1)
                    # Clean up extra newlines
                    new_charter = re.sub(r'\n{3,}', '\n\n', new_charter)
                    return {
                        "before": old_text,
                        "after": "(REMOVED)",
                        "full_new_charter": new_charter
                    }

            return None

        except Exception as e:
            logger.error(f"❌ Error generating preview: {e}")
            return None

    async def _fuzzy_update(self, current_charter: str, parsed_request: Dict) -> Optional[Dict]:
        """Use AI to find and update when exact match fails"""
        if not self.ai_assistant:
            return None

        prompt = f"""You are updating a charter document. The user wants to make this change:
{json.dumps(parsed_request, indent=2)}

Here is the current charter:
{current_charter}

Find the relevant section and apply the change. Return the COMPLETE updated charter with the change applied.
Return ONLY the updated charter text, nothing else."""

        try:
            new_charter = await self.ai_assistant.ask_openai(prompt, "Charter Fuzzy Update", max_tokens=4000)
            if not new_charter:
                new_charter = await self.ai_assistant.ask_anthropic(prompt, "Charter Fuzzy Update", max_tokens=4000)

            if new_charter:
                return {
                    "before": parsed_request.get("old_text", "(Section being modified)"),
                    "after": parsed_request.get("new_text"),
                    "full_new_charter": new_charter
                }
            return None

        except Exception as e:
            logger.error(f"❌ Error in fuzzy update: {e}")
            return None

    def apply_update(
        self,
        new_charter: str,
        user_id: int,
        user_name: str,
        description: str,
        before_text: Optional[str] = None,
        after_text: Optional[str] = None
    ) -> bool:
        """Apply an update to the charter and log it"""
        try:
            # Write the new charter (this also creates a backup)
            success = self.write_charter(new_charter)

            if success:
                # Log the change
                self.add_changelog_entry(
                    user_id=user_id,
                    user_name=user_name,
                    action="update",
                    description=description,
                    before_text=before_text,
                    after_text=after_text
                )
                logger.info(f"✅ Charter updated by {user_name}: {description}")

            return success

        except Exception as e:
            logger.error(f"❌ Error applying update: {e}")
            return False

    async def find_rule_changes_in_messages(
        self,
        messages: List[str],
        channel_name: str = "voting channel"
    ) -> Optional[List[Dict]]:
        """
        Analyze messages to find rule changes, votes, and decisions

        Returns list of:
        - rule: the rule text
        - status: passed/failed/proposed
        - votes_for: count (if available)
        - votes_against: count (if available)
        - context: additional context
        """
        if not self.ai_assistant:
            logger.warning("⚠️ AI assistant not available for message analysis")
            return None

        if not messages:
            return None

        # Join messages for analysis
        messages_text = "\n".join(messages[:100])  # Limit to recent 100

        prompt = f"""You are analyzing a Discord channel called "{channel_name}" for rule changes and votes in a CFB 26 dynasty league.

MESSAGES FROM THE CHANNEL:
{messages_text}

Find any:
1. Rule proposals
2. Votes on rules (passed or failed)
3. Rule changes that were decided
4. Policy updates

For each rule change found, extract:
- The rule/change description
- Whether it passed, failed, or is just proposed
- Vote counts if mentioned
- Any relevant context

Respond in this EXACT JSON format (no markdown, just raw JSON array):
[
    {{
        "rule": "Description of the rule or change",
        "status": "passed|failed|proposed|decided",
        "votes_for": null or number,
        "votes_against": null or number,
        "context": "Any additional context or notes"
    }}
]

If no rule changes are found, respond with: []"""

        try:
            response = await self.ai_assistant.ask_openai(prompt, "Rule Change Finder", max_tokens=2000)
            if not response:
                response = await self.ai_assistant.ask_anthropic(prompt, "Rule Change Finder", max_tokens=2000)

            if not response:
                return None

            # Clean up response
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```\w*\n?', '', response)
                response = re.sub(r'\n?```$', '', response)

            # Parse JSON
            changes = json.loads(response)
            logger.info(f"📜 Found {len(changes)} rule changes in {channel_name}")
            return changes

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse rule changes JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error finding rule changes: {e}")
            return None

    async def generate_charter_updates_from_rules(
        self,
        rule_changes: List[Dict]
    ) -> Optional[List[Dict]]:
        """
        Generate charter update suggestions based on found rule changes

        Returns list of suggested updates with before/after text
        """
        if not self.ai_assistant or not rule_changes:
            return None

        current_charter = self.read_charter()
        if not current_charter:
            return None

        # Filter to only passed/decided rules
        passed_rules = [r for r in rule_changes if r.get("status") in ["passed", "decided"]]

        if not passed_rules:
            return None

        prompt = f"""You are updating a CFB 26 league charter based on rules that were voted on and passed.

CURRENT CHARTER:
{current_charter}

RULES THAT PASSED (need to be added/updated in charter):
{json.dumps(passed_rules, indent=2)}

For each passed rule, determine:
1. Is this a NEW rule that needs to be added?
2. Is this an UPDATE to an existing rule?
3. Where in the charter should it go?

Generate the charter updates needed. Respond in this EXACT JSON format:
[
    {{
        "rule_description": "Brief description of what's being changed",
        "action": "add|update",
        "section": "Which section this belongs to",
        "old_text": "Text to find and replace (null if adding new)",
        "new_text": "The new or updated text to insert"
    }}
]

If no updates are needed (rules already in charter), respond with: []"""

        try:
            response = await self.ai_assistant.ask_openai(prompt, "Charter Update Generator", max_tokens=3000)
            if not response:
                response = await self.ai_assistant.ask_anthropic(prompt, "Charter Update Generator", max_tokens=3000)

            if not response:
                return None

            # Clean up response
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```\w*\n?', '', response)
                response = re.sub(r'\n?```$', '', response)

            updates = json.loads(response)
            logger.info(f"📝 Generated {len(updates)} charter update suggestions")
            return updates

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse charter updates JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error generating charter updates: {e}")
            return None
