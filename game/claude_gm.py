"""Claude Game Master wrapper with persistent session for D&D emulation."""

import asyncio
import json
import re
from typing import Any


class ClaudeGM:
    """Wrapper for Claude CLI with persistent session to act as a D&D Game Master."""

    def __init__(self, claude_path: str = "claude") -> None:
        """Initialize the Claude Game Master.

        Args:
            claude_path: Path to the claude CLI executable.

        """
        self.claude_path = claude_path
        self.process: asyncio.subprocess.Process | None = None
        self.system_prompt = """You are a Dungeons & Dragons 5th Edition Game Master.
Your role is to:
- Guide players through adventures with engaging storytelling
- Manage game mechanics, NPCs, and world events
- Roll dice when needed (format: [1d20+5] = result)
- Track initiative, health, and game state
- Create immersive descriptions and roleplay NPCs
- Be fair but challenging

Keep responses concise but atmospheric. Always stay in character as the GM."""
        self._initialized = False

    async def start_session(self) -> None:
        """Start a persistent Claude CLI session."""
        if self.process and self.process.returncode is None:
            return  # Already running

        # Start claude in interactive mode
        self.process = await asyncio.create_subprocess_exec(
            self.claude_path,
            "--model",
            "claude-3-5-sonnet-20241022",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Initialize with system prompt
        if not self._initialized:
            await self._send_raw(f"System: {self.system_prompt}\n\n")
            self._initialized = True

    async def stop_session(self) -> None:
        """Stop the persistent Claude CLI session."""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            await self.process.wait()
        self.process = None

    async def send_message(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Send a message to Claude and get the response."""
        # Ensure session is started
        await self.start_session()

        # Build the message with context
        full_message = self._build_message(message, context)

        # Send and receive response
        return await self._send_raw(full_message)

    async def _send_raw(self, message: str) -> str:
        """Send raw message to Claude process and get response."""
        if not self.process or self.process.returncode is not None:
            msg = "Claude process not running"
            raise RuntimeError(msg)

        # Write the message
        self.process.stdin.write(message.encode())  # type: ignore[union-attr]
        await self.process.stdin.drain()  # type: ignore[union-attr]

        # Read response until we see a pattern that indicates completion
        response_lines = []
        while True:
            try:
                line = await asyncio.wait_for(
                    self.process.stdout.readline(),  # type: ignore[union-attr]
                    timeout=30.0,
                )
                if not line:
                    break

                decoded_line = line.decode().rstrip()
                response_lines.append(decoded_line)

                # Check if response seems complete (ends with punctuation or similar)
                if decoded_line and decoded_line[-1] in '.!?":':
                    # Read a bit more to ensure we got everything
                    try:
                        extra = await asyncio.wait_for(
                            self.process.stdout.read(100),  # type: ignore[union-attr]
                            timeout=0.5,
                        )
                        if extra:
                            response_lines.append(extra.decode().rstrip())
                    except TimeoutError:
                        pass
                    break

            except TimeoutError:
                break

        return "\n".join(response_lines).strip()

    def _build_message(self, message: str, context: dict[str, Any] | None) -> str:
        """Build the message including context."""
        parts = []

        if context:
            # Add game state context
            if "game_state" in context:
                parts.append(f"Current Game State: {json.dumps(context['game_state'])}")

            # Add recent history (only last 3 to keep context fresh)
            if "history" in context and len(context["history"]) > 0:
                parts.append("Recent History:")
                parts.extend(
                    f"- {entry}" for entry in context["history"][-3:]
                )

        parts.append(f"Player: {message}")
        parts.append("GM: ")

        return "\n".join(parts)

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

    async def __aenter__(self) -> "ClaudeGM":
        """Async context manager entry."""
        await self.start_session()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self.stop_session()
