#!/usr/bin/env python3
"""
Charter Editor Module for CFB 26 League Bot
Handles editing and updating the league charter
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, List
import json

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
