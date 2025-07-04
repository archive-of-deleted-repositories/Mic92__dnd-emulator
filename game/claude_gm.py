"""Claude Game Master wrapper for D&D emulation."""

import asyncio
import json
import re
import tempfile
from pathlib import Path
from typing import Any


class ClaudeGM:
    """Wrapper for Claude CLI to act as a D&D Game Master."""

    def __init__(self, claude_path: str = "claude") -> None:
        """Initialize the Claude Game Master.

        Args:
            claude_path: Path to the claude CLI executable.

        """
        self.claude_path = claude_path
        self.system_prompt = """You are a Dungeons & Dragons 5th Edition Game Master.
Your role is to:
- Guide players through adventures with engaging storytelling
- Manage game mechanics, NPCs, and world events
- Roll dice when needed (format: [1d20+5] = result)
- Track initiative, health, and game state
- Create immersive descriptions and roleplay NPCs
- Be fair but challenging

Keep responses concise but atmospheric. Always stay in character as the GM."""

    async def send_message(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Send a message to Claude and get the response."""
        # Prepare the full prompt with context
        full_prompt = self._build_prompt(message, context)

        # Create a temporary file for the prompt
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(full_prompt)
            temp_file = f.name

        try:
            # Run claude CLI
            return await self._run_claude_command(temp_file)
        finally:
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)

    async def _run_claude_command(self, prompt_file: str) -> str:
        """Execute claude CLI command and return output."""
        # Read the prompt from file
        prompt_content = await asyncio.to_thread(Path(prompt_file).read_text)

        cmd = [
            self.claude_path,
            "--print",
            "--model",
            "claude-3-5-sonnet-20241022",
            prompt_content,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = f"Claude CLI error: {stderr.decode()}"
            raise RuntimeError(error_msg)

        return stdout.decode().strip()

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

        return {
            "response": response,
            "dice_rolls": [
                {"notation": roll[0], "result": int(roll[1])} for roll in rolls
            ],
        }
