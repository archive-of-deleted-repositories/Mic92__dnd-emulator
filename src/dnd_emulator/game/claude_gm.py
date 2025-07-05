"""Claude Game Master wrapper using streaming JSON output."""

import asyncio
import json
import logging
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
        self.has_session = False  # Track if we have an active session
        self.session_id: str | None = None  # Store session ID if available
        self.logger = logging.getLogger(__name__)

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
        return response

    async def _execute_claude(self, prompt: str) -> str:
        """Execute claude CLI and return the response."""
        cmd = self._build_command(prompt)

        if self.has_session:
            self.logger.info("Continuing session %s", self.session_id)
        else:
            self.logger.info("Starting new Claude session")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
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

        # Add resume/continue flag based on session state
        if self.session_id:
            # Resume a specific Claude session
            cmd.extend(["--resume", self.session_id])
        elif self.has_session:
            # Continue the most recent session
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

            # Check for session ID in init message
            if json_msg.get("type") == "system" and json_msg.get("subtype") == "init":
                if "session_id" in json_msg:
                    self.session_id = json_msg["session_id"]
                    self.has_session = True
                    self.logger.debug("Session initialized: %s", self.session_id)

            # Extract text content from content messages
            elif json_msg.get("type") == "content" and "text" in json_msg:
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
        """Build the full prompt including system prompt and context."""
        parts = [f"System: {self.system_prompt}"]

        if context:
            # Add game state context
            if "game_state" in context:
                parts.append(f"Current Game State: {json.dumps(context['game_state'])}")

            # Add recent history
            if "history" in context:
                parts.append("Recent History:")
                parts.extend(
                    f"- {entry}" for entry in context["history"][-5:]
                )  # Last 5 messages

        parts.append(f"Player: {message}")
        parts.append("GM:")

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

    def reset_session(self) -> None:
        """Reset the session, forcing a new conversation on next message."""
        if self.session_id:
            self.logger.info("Resetting session %s", self.session_id)
        self.has_session = False
        self.session_id = None

    def set_session(self, session_id: str | None) -> None:
        """Set a specific Claude session to resume.

        Args:
            session_id: The Claude session ID to resume, or None for new session.

        """
        if session_id:
            self.logger.info("Setting session to resume: %s", session_id)
            self.session_id = session_id
            self.has_session = False  # Will use --resume instead of --continue
        else:
            self.reset_session()
