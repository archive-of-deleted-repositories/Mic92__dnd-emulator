"""Claude Game Master wrapper using streaming JSON output."""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any


class ClaudeGM:
    """Wrapper for Claude CLI to act as a D&D Game Master."""

    RESPONSE_LOG_LIMIT = 200  # Max characters to log from responses

    def __init__(self, claude_path: str = "claude") -> None:
        """Initialize the Claude Game Master.

        Args:
            claude_path: Path to the claude CLI executable.

        """
        self.claude_path = claude_path
        self.session_id: str | None = None  # Store session ID for directory
        self.claude_session_id: str | None = None  # Store Claude's session ID
        self.has_sent_message = (
            False  # Track if we've sent a message in current session
        )
        self.logger = logging.getLogger(__name__)

        # Set up base directory for sessions
        xdg_data_home = os.environ.get(
            "XDG_DATA_HOME",
            str(Path.home() / ".local" / "share"),
        )
        self.sessions_dir = Path(xdg_data_home) / "dnd-emulator" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Load system prompt from file
        prompt_file = Path(__file__).parent / "gm_system_prompt.txt"
        self.system_prompt = prompt_file.read_text(encoding="utf-8").strip()

    async def send_message(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Send a message to Claude and get the response."""
        self.logger.info("Player message: %s", message)

        # Build the full prompt with context
        full_prompt = self._build_prompt(message, context)

        # Execute claude with streaming JSON output
        response = await self._execute_claude(full_prompt)

        truncated = (
            response[: self.RESPONSE_LOG_LIMIT] + "..."
            if len(response) > self.RESPONSE_LOG_LIMIT
            else response
        )
        self.logger.info("GM response: %s", truncated)

        # Mark that we've sent a message in this session
        self.has_sent_message = True

        return response

    async def _execute_claude(self, prompt: str) -> str:
        """Execute claude CLI and return the response."""
        cmd = self._build_command(prompt)

        # Each session runs in its own directory
        if not self.session_id:
            msg = "No session ID set"
            raise RuntimeError(msg)

        session_dir = self.sessions_dir / self.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info("Running in session directory: %s", session_dir)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(session_dir),
        )

        response_parts = await self._read_streaming_response(process)

        # Wait for process to complete
        await process.wait()

        if process.returncode != 0:
            stderr_output = ""
            if process.stderr:
                stderr_output = (await process.stderr.read()).decode()
            error_msg = f"Claude CLI error (code {process.returncode}): {stderr_output}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        return "".join(response_parts).strip()

    def _build_command(self, prompt: str) -> list[str]:
        """Build the command line arguments for Claude."""
        cmd = [self.claude_path]

        # Use --resume with session ID if we have one from a previous run
        if self.claude_session_id and not self.has_sent_message:
            cmd.extend(["--resume", self.claude_session_id])
        # Use --continue for subsequent messages in the same process
        elif self.has_sent_message:
            cmd.append("--continue")

        cmd.extend(
            [
                "--print",
                "--verbose",
                "--allowedTools",
                "WebSearch",
                "--model",
                "claude-3-5-sonnet-20241022",
                "--output-format",
                "stream-json",
                prompt,
            ],
        )

        # Log the command for debugging
        cmd_preview_len = 3
        if len(cmd) > cmd_preview_len:
            cmd_str = " ".join([*cmd[:cmd_preview_len], "..."])
        else:
            cmd_str = " ".join(cmd)
        self.logger.info("Claude command: %s", cmd_str)

        return cmd

    async def _read_streaming_response(
        self,
        process: asyncio.subprocess.Process,
    ) -> list[str]:
        """Read and parse streaming JSON response from Claude."""
        response_parts = []

        if process.stdout:
            async for line in process.stdout:
                line_str = line.decode("utf-8").strip()
                if line_str:
                    parts = self._parse_json_line(line_str)
                    response_parts.extend(parts)

        return response_parts

    def _parse_json_line(self, line_str: str) -> list[str]:
        """Parse a single JSON line from Claude's output."""
        parts = []
        try:
            json_msg = json.loads(line_str)

            # Extract text content from content messages
            if json_msg.get("type") == "content" and "text" in json_msg:
                parts.append(json_msg["text"])

            # Extract text from assistant messages
            elif json_msg.get("type") == "assistant" and "message" in json_msg:
                msg = json_msg["message"]
                if msg.get("content"):
                    parts.extend(self._extract_content(msg["content"]))

            # Handle complete message format
            elif (
                json_msg.get("type") == "message"
                and json_msg.get("role") == "assistant"
                and "content" in json_msg
            ):
                parts.extend(self._extract_content(json_msg["content"]))

        except json.JSONDecodeError:
            # If it's not JSON, it might be raw output in some cases
            pass

        return parts

    def _extract_content(
        self,
        content: str | list[str | dict[str, Any]],
    ) -> list[str]:
        """Extract text content from various content formats."""
        parts = []
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    parts.append(item)
        return parts

    def _build_prompt(self, message: str, context: dict[str, Any] | None) -> str:
        """Build the prompt for Claude.

        For existing sessions, Claude maintains context so we only send the message.
        For new sessions, we include the system prompt to establish the context.
        """
        # If resuming an existing Claude session or continuing in same process
        if self.has_sent_message or self.claude_session_id:
            return f"<player>{message}</player>"

        # For new sessions, include system prompt
        parts = [f"<system>{self.system_prompt}</system>"]

        # Add initial game state if provided
        if context and "game_state" in context:
            parts.append(
                f"<game_state>{json.dumps(context['game_state'])}</game_state>"
            )

        parts.append(f"<player>{message}</player>")
        parts.append("<gm>")

        return "\n\n".join(parts)

    def parse_dice_rolls(self, response: str) -> dict[str, Any]:
        """Parse dice roll notations from the response."""
        dice_pattern = r"\[(\d+d\d+(?:[+-]\d+)?)\]\s*=\s*(\d+)"
        rolls = re.findall(dice_pattern, response)

        if rolls:
            dice_results = [f"{r[0]}={r[1]}" for r in rolls]
            self.logger.info("Dice rolls detected: %s", dice_results)

        return {
            "response": response,
            "dice_rolls": [
                {"notation": roll[0], "result": int(roll[1])} for roll in rolls
            ],
        }

    def set_session(self, session_name: str) -> None:
        """Set the session to use.

        Args:
            session_name: The session name (used as directory name).

        """
        self.logger.info("Setting session: %s", session_name)
        self.session_id = session_name
        self.has_sent_message = False  # Reset for new session

        # Check if there's an existing Claude session for this directory
        self.claude_session_id = self._find_claude_session_id()
        if self.claude_session_id:
            self.logger.info(
                "Found existing Claude session: %s", self.claude_session_id
            )

    def _find_claude_session_id(self) -> str | None:
        """Find the most recent Claude session ID for the current session directory."""
        if not self.session_id:
            return None

        # Claude stores sessions in ~/.claude/projects/ based on working directory
        session_dir = self.sessions_dir / self.session_id
        # Convert path to Claude's project directory naming
        # Claude replaces "/" "_" and "." with "-"
        project_name = (
            str(session_dir).replace("/", "-").replace("_", "-").replace(".", "-")
        )
        # Claude keeps the leading dash
        if not project_name.startswith("-"):
            project_name = "-" + project_name

        claude_project_dir = Path.home() / ".claude" / "projects" / project_name

        self.logger.debug("Looking for Claude project dir: %s", claude_project_dir)

        if not claude_project_dir.exists():
            self.logger.debug("Claude project dir does not exist")
            return None

        # Find the most recent session file
        session_files = list(claude_project_dir.glob("*.jsonl"))
        if not session_files:
            self.logger.debug("No session files found")
            return None

        self.logger.debug("Found %d session files", len(session_files))

        # Get the most recent file
        newest_file = max(session_files, key=lambda f: f.stat().st_mtime)
        # The session ID is the filename without extension
        session_id = newest_file.stem
        self.logger.debug("Most recent session ID: %s", session_id)
        return session_id
