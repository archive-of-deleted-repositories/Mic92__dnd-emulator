"""Session manager for Claude CLI sessions."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ClaudeSessionManager:
    """Manages Claude CLI session files."""

    def __init__(self, project_path: str | None = None) -> None:
        """Initialize the session manager.

        Args:
            project_path: Path to the project. If None, uses current working directory.

        """
        self.project_path = Path(project_path or Path.cwd())
        self.claude_dir = Path.home() / ".claude"
        self.project_sessions_dir = self._get_project_sessions_dir()

    def _get_project_sessions_dir(self) -> Path:
        """Get the Claude sessions directory for this project."""
        # Claude encodes the project path by replacing / with -
        encoded_path = str(self.project_path).replace("/", "-")
        return self.claude_dir / "projects" / encoded_path

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all available Claude sessions for this project."""
        sessions: list[dict[str, Any]] = []

        if not self.project_sessions_dir.exists():
            logger.warning(
                "No Claude sessions directory found at %s",
                self.project_sessions_dir,
            )
            return sessions

        # Find all JSONL files in the project sessions directory
        for session_file in self.project_sessions_dir.glob("*.jsonl"):
            try:
                session_info = self._parse_session_file(session_file)
                if session_info:
                    # Remove messages from list response to reduce data size
                    session_info.pop("messages", None)
                    sessions.append(session_info)
            except (json.JSONDecodeError, OSError):
                logger.exception(
                    "Error parsing session file %s",
                    session_file,
                )

        # Sort by last activity (most recent first)
        sessions.sort(key=lambda s: s["last_activity"], reverse=True)
        return sessions

    def _extract_message_content(self, content: str | list[dict[str, Any]]) -> str:
        """Extract text content from Claude message format."""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            return " ".join(text_parts)

        return ""

    def _extract_player_message(self, content: str) -> str:
        """Extract player message from formatted content."""
        if "Player:" in content:
            player_part = content.split("Player:")[-1].split("\n")[0].strip()
            return player_part[:100]  # Truncate long messages
        return content[:100]

    def _parse_session_file(self, session_file: Path) -> dict[str, Any] | None:
        """Parse a Claude session JSONL file to extract session info."""
        session_id = session_file.stem  # Filename without .jsonl extension

        # Read the file line by line
        lines = session_file.read_text(encoding="utf-8").strip().split("\n")
        if not lines:
            return None

        # Initialize session data
        summary = self._extract_summary(lines[0])

        # Process all entries
        parsed_data = self._process_session_entries(lines)

        # Get last activity time
        last_activity = parsed_data["last_activity"] or self._get_file_mtime(
            session_file
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

    def _extract_summary(self, first_line: str) -> str:
        """Extract summary from the first line of session file."""
        try:
            data = json.loads(first_line)
            return data.get("summary", "No summary available")
        except json.JSONDecodeError:
            return "No summary available"

    def _get_file_mtime(self, file_path: Path) -> datetime:
        """Get file modification time as datetime."""
        stat = file_path.stat()
        return datetime.fromtimestamp(stat.st_mtime, tz=UTC)

    def _process_session_entries(self, lines: list[str]) -> dict[str, Any]:
        """Process all entries in a session file."""
        result = {
            "first_message": None,
            "last_activity": None,
            "message_count": 0,
            "messages": [],
        }

        for line in lines:
            try:
                entry = json.loads(line)
                self._process_single_entry(entry, result)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        return result

    def _process_single_entry(
        self, entry: dict[str, Any], result: dict[str, Any]
    ) -> None:
        """Process a single entry from the session file."""
        # Handle messages
        if entry.get("type") in ["user", "assistant"]:
            result["message_count"] += 1
            self._extract_and_append_message(entry, result["messages"])

            # Find first user message
            if entry.get("type") == "user" and result["first_message"] is None:
                self._set_first_user_message(entry, result)

        # Track timestamps
        self._update_last_activity(entry, result)

    def _extract_and_append_message(
        self, entry: dict[str, Any], messages: list[dict[str, Any]]
    ) -> None:
        """Extract message data and append to messages list."""
        message_data = entry.get("message", {})
        if message_data.get("role") in ["user", "assistant"]:
            content = self._extract_message_content(
                message_data.get("content", ""),
            )

            messages.append(
                {
                    "role": message_data.get("role"),
                    "content": content,
                    "timestamp": entry.get("timestamp", ""),
                    "uuid": entry.get("uuid", ""),
                }
            )

    def _set_first_user_message(
        self, entry: dict[str, Any], result: dict[str, Any]
    ) -> None:
        """Set the first user message in the result."""
        message_content = entry.get("message", {}).get("content")
        if message_content:
            content = self._extract_message_content(message_content)
            result["first_message"] = self._extract_player_message(content)

    def _update_last_activity(
        self, entry: dict[str, Any], result: dict[str, Any]
    ) -> None:
        """Update last activity timestamp."""
        if "timestamp" in entry:
            timestamp = datetime.fromisoformat(entry["timestamp"])
            if result["last_activity"] is None or timestamp > result["last_activity"]:
                result["last_activity"] = timestamp

    def get_session_file_path(self, session_id: str) -> Path | None:
        """Get the file path for a specific session ID."""
        session_file = self.project_sessions_dir / f"{session_id}.jsonl"
        return session_file if session_file.exists() else None

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self.get_session_file_path(session_id) is not None

    def get_session_with_messages(self, session_id: str) -> dict[str, Any] | None:
        """Get a specific session with all its messages."""
        session_file = self.get_session_file_path(session_id)
        if not session_file:
            return None

        return self._parse_session_file(session_file)
