"""Test suite for Claude GM functionality using real Claude CLI."""

import pytest

from dnd_emulator.game.claude_gm import ClaudeGM


class TestClaudeGM:
    """Test cases for ClaudeGM class with real Claude CLI."""

    @pytest.fixture
    def gm(self) -> ClaudeGM:
        """Create a ClaudeGM instance."""
        return ClaudeGM()


    @pytest.mark.asyncio
    async def test_send_message_simple(
        self,
        gm: ClaudeGM,
    ) -> None:
        """Test sending a simple message without context."""
        # Reset session to ensure clean state
        gm.reset_session()

        # Send a simple test message
        response = await gm.send_message(
            "Reply with exactly: 'Hello from Claude GM'",
            None,
        )

        # Verify we got a response
        assert isinstance(response, str)
        assert len(response) > 0

        # Verify session was established
        assert gm.has_session
        assert gm.session_id is not None

    @pytest.mark.asyncio
    async def test_send_message_with_context(
        self,
        gm: ClaudeGM,
    ) -> None:
        """Test sending a message with D&D context."""
        # Test context
        context = {
            "game_state": {
                "players": ["Thorin the Dwarf Fighter"],
                "current_scene": "Tavern",
                "initiative_order": [],
            },
            "history": [
                "Player: I'm Thorin, a dwarf fighter",
                "GM: Welcome Thorin! You find yourself in the Prancing Pony tavern.",
            ],
        }

        # Send message with context
        response = await gm.send_message(
            "I approach the bartender and ask about any quests or rumors",
            context,
        )

        # Verify response
        assert isinstance(response, str)
        assert len(response) > 0

        # Parse for dice rolls
        parsed = gm.parse_dice_rolls(response)
        assert "response" in parsed
        assert "dice_rolls" in parsed
        assert isinstance(parsed["dice_rolls"], list)
