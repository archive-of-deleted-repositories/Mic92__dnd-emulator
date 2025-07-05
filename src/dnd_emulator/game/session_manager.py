"""Session manager for D&D Emulator sessions."""

import json
import logging
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ClaudeSessionManager:
    """Manages D&D Emulator session directories."""

    def __init__(self) -> None:
        """Initialize the session manager."""
        # Set up base directory for sessions
        xdg_data_home = os.environ.get(
            "XDG_DATA_HOME",
            str(Path.home() / ".local" / "share"),
        )
        self.sessions_dir = Path(xdg_data_home) / "dnd-emulator" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all available D&D sessions."""
        sessions: list[dict[str, Any]] = []

        # Iterate through each session directory
        for session_dir in self.sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue

            # Find the newest Claude session file
            # Claude stores sessions in ~/.claude/projects/{encoded-path}/
            # where the path is encoded by replacing "/" "_" and "." with "-"
            project_name = (
                str(session_dir).replace("/", "-").replace("_", "-").replace(".", "-")
            )
            if not project_name.startswith("-"):
                project_name = "-" + project_name

            claude_project_dir = Path.home() / ".claude" / "projects" / project_name
            if not claude_project_dir.exists():
                # No Claude sessions yet in this directory
                sessions.append(
                    {
                        "session_id": session_dir.name,
                        "summary": f"Session: {session_dir.name}",
                        "first_message": "No messages yet",
                        "message_count": 0,
                        "last_activity": datetime.fromtimestamp(
                            session_dir.stat().st_mtime,
                            tz=UTC,
                        ).isoformat(),
                    },
                )
                continue

            # Find the newest JSONL file
            jsonl_files = list(claude_project_dir.glob("*.jsonl"))
            if not jsonl_files:
                continue

            newest_file = max(jsonl_files, key=lambda f: f.stat().st_mtime)

            session_info = self._parse_session_file(newest_file, session_dir.name)
            if session_info:
                # Remove messages from list response to reduce data size
                session_info.pop("messages", None)
                sessions.append(session_info)

        # Sort by last activity (most recent first)
        sessions.sort(key=lambda s: s["last_activity"], reverse=True)
        return sessions

    def _extract_message_content(self, content: str | list[dict[str, Any]]) -> str:
        """Extract text content from Claude message format."""
        if isinstance(content, str):
            return content
        text_parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return " ".join(text_parts)

    def _extract_player_message(self, content: str) -> str:
        """Extract player message from formatted content."""
        # First try XML tags
        if "<player>" in content and "</player>" in content:
            player_match = re.search(r"<player>(.*?)</player>", content, re.DOTALL)
            if player_match:
                return player_match.group(1).strip()[:100]
        # Fallback to old format
        elif "Player:" in content:
            player_part = content.split("Player:")[-1].split("\n")[0].strip()
            return player_part[:100]  # Truncate long messages
        return content[:100]

    def _parse_session_file(
        self,
        session_file: Path,
        session_name: str,
    ) -> dict[str, Any] | None:
        """Parse a Claude session JSONL file to extract session info."""
        session_id = session_name  # Use the directory name as session ID

        # Read the file line by line
        lines = session_file.read_text(encoding="utf-8").strip().split("\n")
        if not lines:
            return None

        # Initialize session data
        summary = self._extract_summary(lines[0], session_name)

        # Process all entries
        parsed_data = self._process_session_entries(lines)

        # Get last activity time
        last_activity = parsed_data["last_activity"] or self._get_file_mtime(
            session_file,
        )

        return {
            "session_id": session_id,
            "summary": summary,
            "first_message": parsed_data["first_message"] or "No messages",
            "message_count": parsed_data["message_count"],
            "last_activity": last_activity.isoformat(),
            "file_path": str(session_file),
            "messages": parsed_data["messages"],
        }

    def _extract_summary(self, first_line: str, session_name: str) -> str:
        """Extract summary from the first line of session file."""
        try:
            data = json.loads(first_line)
            summary = data.get("summary")
            if summary:
                return str(summary)
            # Fallback to session name
            return session_name.replace("_", " ").title()
        except json.JSONDecodeError:
            return session_name.replace("_", " ").title()

    def _get_file_mtime(self, file_path: Path) -> datetime:
        """Get file modification time as datetime."""
        stat = file_path.stat()
        return datetime.fromtimestamp(stat.st_mtime, tz=UTC)

    def _process_session_entries(self, lines: list[str]) -> dict[str, Any]:
        """Process all entries in a session file."""
        result: dict[str, Any] = {
            "first_message": None,
            "last_activity": None,
            "message_count": 0,
            "messages": [],
        }

        for i, line in enumerate(lines):
            entry = json.loads(line)
            if entry.get("type") in ["user", "assistant"]:
                logger.debug(
                    "Line %d: Processing entry type: %s", i + 1, entry.get("type")
                )
            self._process_single_entry(entry, result)

        logger.debug("Processed %d messages total", result["message_count"])
        return result

    def _process_single_entry(
        self,
        entry: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Process a single entry from the session file."""
        # Handle messages
        if entry.get("type") in ["user", "assistant"]:
            # Extract and append message (may be filtered)
            # This will increment message_count only if message is not filtered
            self._extract_and_append_message(entry, result)

            # Find first user message
            if entry.get("type") == "user" and result["first_message"] is None:
                self._set_first_user_message(entry, result)

        # Track timestamps
        self._update_last_activity(entry, result)

    def _extract_and_append_message(
        self,
        entry: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Extract message data and append to messages list."""
        message_data = entry.get("message", {})
        messages = result["messages"]

        if message_data.get("role") in ["user", "assistant"]:
            content = self._extract_message_content(
                message_data.get("content", ""),
            )
            logger.debug(
                "Extracted content (%d chars): %s...",
                len(content) if content else 0,
                content[:100] if content else "None",
            )

            # Extract actual player message from compound messages
            # First try XML tags
            if "<player>" in content and "</player>" in content:
                # Extract content between player tags
                player_match = re.search(r"<player>(.*?)</player>", content, re.DOTALL)
                if player_match:
                    content = player_match.group(1).strip()
                else:
                    # No player content, skip this message
                    return
            elif "<system>" in content and "</system>" in content:
                # Skip pure system messages
                return
            # Fallback to old format for existing sessions
            elif content.startswith("System:") and "Player:" in content:
                # Extract just the player part
                player_part = content.split("Player:")[-1].split("GM:")[0].strip()
                if player_part:
                    content = player_part
                else:
                    # No player content, skip this message
                    return
            elif content.startswith("System: You are a Dungeons & Dragons"):
                # Skip pure system prompts
                return

            # Only count and append if we have actual content
            messages.append(
                {
                    "role": message_data.get("role"),
                    "content": content,
                    "timestamp": entry.get("timestamp", ""),
                    "uuid": entry.get("uuid", ""),
                },
            )
            result["message_count"] += 1

    def _set_first_user_message(
        self,
        entry: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Set the first user message in the result."""
        message_content = entry.get("message", {}).get("content")
        if message_content:
            content = self._extract_message_content(message_content)
            result["first_message"] = self._extract_player_message(content)

    def _update_last_activity(
        self,
        entry: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Update last activity timestamp."""
        if "timestamp" in entry:
            timestamp = datetime.fromisoformat(entry["timestamp"])
            if result["last_activity"] is None or timestamp > result["last_activity"]:
                result["last_activity"] = timestamp

    def session_exists(self, session_id: str) -> bool:
        """Check if a session directory exists."""
        session_dir = self.sessions_dir / session_id
        return session_dir.exists() and session_dir.is_dir()

    def get_session_with_messages(self, session_id: str) -> dict[str, Any] | None:
        """Get a specific session with all its messages."""
        session_dir = self.sessions_dir / session_id
        if not session_dir.exists():
            return None

        # Find the newest Claude session file
        # Claude stores sessions in ~/.claude/projects/{encoded-path}/
        project_name = (
            str(session_dir).replace("/", "-").replace("_", "-").replace(".", "-")
        )
        if not project_name.startswith("-"):
            project_name = "-" + project_name

        claude_project_dir = Path.home() / ".claude" / "projects" / project_name
        if not claude_project_dir.exists():
            return {
                "session_id": session_id,
                "summary": f"Session: {session_id}",
                "first_message": "No messages yet",
                "message_count": 0,
                "last_activity": datetime.fromtimestamp(
                    session_dir.stat().st_mtime,
                    tz=UTC,
                ).isoformat(),
                "messages": [],
            }

        jsonl_files = list(claude_project_dir.glob("*.jsonl"))
        if not jsonl_files:
            return None

        newest_file = max(jsonl_files, key=lambda f: f.stat().st_mtime)
        return self._parse_session_file(newest_file, session_id)
