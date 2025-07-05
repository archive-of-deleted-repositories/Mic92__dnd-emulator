"""Test suite for Claude session manager."""

import shutil
from pathlib import Path

import pytest

from dnd_emulator.game.session_manager import ClaudeSessionManager


class TestClaudeSessionManager:
    """Test cases for ClaudeSessionManager class."""

    @pytest.fixture
    def test_sessions_dir(self, tmp_path: Path) -> Path:
        """Create a test sessions directory."""
        # Create test session directory structure
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        # Create test session directory
        test_session = sessions_dir / "test_dnd_adventure"
        test_session.mkdir()

        return sessions_dir

    @pytest.fixture
    def mock_claude_project_dir(self, test_sessions_dir: Path) -> Path:
        """Set up mock Claude session directory with our test assets."""
        # Create the .claude/sessions directory inside the test session
        test_session_dir = test_sessions_dir / "test_dnd_adventure"
        claude_sessions_dir = test_session_dir / ".claude" / "sessions"
        claude_sessions_dir.mkdir(parents=True)

        # Copy our test session files
        assets_dir = Path(__file__).parent / "assets" / "claude_sessions"
        files_copied = 0
        for session_file in assets_dir.glob("*.jsonl"):
            shutil.copy(session_file, claude_sessions_dir)
            files_copied += 1
        print(f"Copied {files_copied} files to {claude_sessions_dir}")

        return claude_sessions_dir

    @pytest.fixture
    def session_manager(
        self,
        test_sessions_dir: Path,
        mock_claude_project_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> ClaudeSessionManager:
        """Create a session manager with test data."""
        manager = ClaudeSessionManager()
        # Monkey patch the sessions directory
        monkeypatch.setattr(manager, "sessions_dir", test_sessions_dir)
        return manager

    def test_list_and_parse_sessions(
        self,
        session_manager: ClaudeSessionManager,
    ) -> None:
        """Test listing and parsing Claude sessions."""
        sessions = session_manager.list_sessions()

        # Should find our test session
        assert len(sessions) > 0, "Should find at least one session"

        # Debug: print all sessions
        print(f"Session manager looking in: {session_manager.sessions_dir}")
        for s in sessions:
            print(f"Found session: {s['session_id']} with {s['message_count']} messages")

        # Find our test session
        test_session = None
        for session in sessions:
            if session["session_id"] == "test_dnd_adventure":
                test_session = session
                break

        assert test_session is not None, "Should find test_dnd_adventure session"

        # Verify session structure
        assert "session_id" in test_session
        assert "summary" in test_session
        assert "first_message" in test_session
        assert "message_count" in test_session
        assert "last_activity" in test_session

        # Verify content
        assert test_session["session_id"] == "test_dnd_adventure"
        assert test_session["message_count"] > 0

        # Check for D&D content in summary or first message
        assert any(
            [
                "D&D" in test_session.get("summary", ""),
                "Thorin" in test_session.get("first_message", ""),
                "adventure" in test_session.get("summary", "").lower(),
            ]
        ), (
            f"Should find D&D content. "
            f"Summary: {test_session.get('summary')}, "
            f"First message: {test_session.get('first_message')}"
        )

        # Message count should be positive for our test session
        min_expected_messages = 5
        assert test_session["message_count"] >= min_expected_messages, (
            f"Should have at least {min_expected_messages} messages from our test "
            f"conversation, got {test_session['message_count']}"
        )

        # Summary and first_message should be strings
        assert isinstance(test_session["summary"], str)
        assert isinstance(test_session["first_message"], str)

        # Test session existence
        assert session_manager.session_exists("test_dnd_adventure")
        assert not session_manager.session_exists("non-existent-session")

    def test_get_session_with_messages(
        self,
        session_manager: ClaudeSessionManager,
    ) -> None:
        """Test getting a session with its messages."""
        # Get our test session with messages
        session_data = session_manager.get_session_with_messages("test_dnd_adventure")

        assert session_data is not None
        assert session_data["session_id"] == "test_dnd_adventure"
        assert "messages" in session_data

        # Verify messages structure
        messages = session_data["messages"]
        assert isinstance(messages, list)
        min_expected_messages = 5
        assert len(messages) >= min_expected_messages, (
            f"Should have at least {min_expected_messages} messages from our "
            f"conversation, got {len(messages)}"
        )

        # Check message structure
        for message in messages:
            assert "role" in message
            assert "content" in message
            assert "timestamp" in message
            assert "uuid" in message

            # Role should be either user or assistant
            assert message["role"] in ["user", "assistant"]

            # Content should be a non-empty string
            assert isinstance(message["content"], str)
            assert len(message["content"]) > 0

        # Verify our specific conversation content
        # Find the first user message about Thorin
        thorin_message = None
        for msg in messages:
            if msg["role"] == "user" and "Thorin" in msg["content"]:
                thorin_message = msg
                break

        assert thorin_message is not None, "Should find Thorin's introduction message"
        assert any(
            [
                "dwarf" in thorin_message["content"],
                "cleric" in thorin_message["content"],
            ]
        ), "Should mention dwarf or cleric"

        # Find GM response
        gm_response = None
        for i, msg in enumerate(messages):
            if msg["role"] == "assistant" and i > 0:
                gm_response = msg
                break

        assert gm_response is not None, "Should find at least one GM response"

        # Number of messages should match message_count
        assert len(messages) == session_data["message_count"]

    def test_get_non_existent_session_with_messages(
        self,
        session_manager: ClaudeSessionManager,
    ) -> None:
        """Test getting messages for a non-existent session."""
        session_data = session_manager.get_session_with_messages("non-existent-id")
        assert session_data is None

    def test_session_sorting(
        self,
        session_manager: ClaudeSessionManager,
    ) -> None:
        """Test that sessions are sorted by last activity."""
        sessions = session_manager.list_sessions()

        if len(sessions) > 1:
            # Check that sessions are sorted by last activity (most recent first)
            for i in range(1, len(sessions)):
                assert (
                    sessions[i - 1]["last_activity"] >= sessions[i]["last_activity"]
                ), "Sessions should be sorted by last activity (most recent first)"

    def test_message_filtering(
        self,
        session_manager: ClaudeSessionManager,
    ) -> None:
        """Test that system prompts and non-D&D messages are filtered out."""
        session_data = session_manager.get_session_with_messages("test_dnd_adventure")

        assert session_data is not None
        messages = session_data["messages"]

        # Check that no message starts with system prompt
        for msg in messages:
            assert not msg["content"].startswith(
                "System: You are a Dungeons & Dragons"
            ), "System prompts should be filtered out"

        # All messages should be game-related
        for msg in messages:
            if msg["role"] == "user":
                # User messages should be player actions/dialogue
                assert not msg["content"].startswith("System:"), (
                    "User messages shouldn't have System: prefix"
                )

    def test_multiple_sessions_in_one_file(
        self,
        session_manager: ClaudeSessionManager,
    ) -> None:
        """Test that we correctly pick the newest session file when multiple exist."""
        sessions = session_manager.list_sessions()

        # Our test assets have multiple session files
        test_session = next(
            (s for s in sessions if s["session_id"] == "test_dnd_adventure"), None
        )

        if test_session:
            # Should have picked the file with the most recent content
            assert "file_path" in test_session
            assert test_session["file_path"].endswith(".jsonl")
