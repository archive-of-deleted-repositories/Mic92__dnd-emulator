"""Test suite for Claude GM functionality using real Claude CLI."""

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

from dnd_emulator.game.claude_gm import ClaudeGM


class TestClaudeGM:
    """Test cases for ClaudeGM class with real Claude CLI."""

    @pytest.fixture(autouse=True)
    def cleanup_sessions(self) -> Generator[None]:
        """Clean up test session directories before tests."""
        # Clean up before test
        self._cleanup_test_sessions()

        return

    def _cleanup_test_sessions(self) -> None:
        """Remove test session directories."""
        # Clean up our session directories
        sessions_base = Path.home() / ".local" / "share" / "dnd-emulator" / "sessions"
        test_sessions = [
            "test_simple_session",
            "test_context_session",
            "test_resume_session",
            "test_session_1",
            "test_session_2",
        ]

        for session in test_sessions:
            session_dir = sessions_base / session
            if session_dir.exists():
                shutil.rmtree(session_dir)

        # Clean up Claude project directories for test sessions
        claude_projects = Path.home() / ".claude" / "projects"
        if claude_projects.exists():
            for session in test_sessions:
                # Convert session name to Claude project format
                project_name = (
                    f"-Users-joerg--local-share-dnd-emulator-sessions-"
                    f"{session.replace('_', '-')}"
                )
                project_dir = claude_projects / project_name
                if project_dir.exists():
                    shutil.rmtree(project_dir)

    @pytest.fixture
    def gm(self) -> ClaudeGM:
        """Create a ClaudeGM instance."""
        return ClaudeGM()

    @pytest.mark.asyncio
    async def test_send_message_simple(
        self,
        gm: ClaudeGM,
    ) -> None:
        """Test sending a simple message without context and a follow-up."""
        # Set a test session
        test_session = "test_simple_session"
        gm.set_session(test_session)

        # Send a simple test message
        response = await gm.send_message(
            "Reply with exactly: 'Hello from Claude GM'",
            None,
        )

        # Verify we got a response
        assert isinstance(response, str)
        assert len(response) > 0

        # Verify session was marked as having sent a message
        assert gm.has_sent_message

        # Send a follow-up message to test session continuation
        follow_up_response = await gm.send_message(
            "Now reply with exactly: 'Session continues'",
            None,
        )

        # Verify follow-up response
        assert isinstance(follow_up_response, str)
        assert len(follow_up_response) > 0

        # Session should still be active
        assert gm.has_sent_message

    @pytest.mark.asyncio
    async def test_send_message_with_context(
        self,
        gm: ClaudeGM,
    ) -> None:
        """Test sending a message with D&D context."""
        # Set a test session
        test_session = "test_context_session"
        gm.set_session(test_session)

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

    @pytest.mark.asyncio
    async def test_resume_session(
        self,
        gm: ClaudeGM,
    ) -> None:
        """Test resuming a specific Claude session."""
        # Use a specific test session
        test_session = "test_resume_session"
        gm.set_session(test_session)

        # Send first message to create a session
        first_response = await gm.send_message(
            "Remember the number 42. Reply with: 'I will remember 42'",
            None,
        )

        assert isinstance(first_response, str)
        assert gm.has_sent_message
        assert gm.session_id == test_session

        # Create a new GM instance (simulating a new connection)
        new_gm = ClaudeGM()

        # Set the same session to resume
        new_gm.set_session(test_session)

        # Verify session is set up for resumption
        assert not new_gm.has_sent_message  # Should be False initially
        assert new_gm.session_id == test_session

        # Resume the session and ask about the number
        resume_response = await new_gm.send_message(
            "What number did I ask you to remember? Reply with just the number.",
            None,
        )

        assert isinstance(resume_response, str)

        # Check if the session has been created
        session_dir = (
            Path.home()
            / ".local"
            / "share"
            / "dnd-emulator"
            / "sessions"
            / test_session
        )
        claude_dir = session_dir / ".claude" / "sessions"
        if claude_dir.exists():
            list(claude_dir.glob("*.jsonl"))

        # The response should contain '42' if session resumption works
        assert "42" in resume_response

        # After resuming, we should have the session marked as active
        assert new_gm.has_sent_message
        assert new_gm.session_id == test_session
