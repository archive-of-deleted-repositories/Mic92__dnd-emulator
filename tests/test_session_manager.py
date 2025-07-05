"""Test suite for Claude session manager."""

from pathlib import Path

import pytest

from dnd_emulator.game.session_manager import ClaudeSessionManager


class TestClaudeSessionManager:
    """Test cases for ClaudeSessionManager class."""

    @pytest.fixture
    def test_sessions_dir(self) -> Path:
        """Get the test sessions directory."""
        return Path(__file__).parent / "assets" / "claude_sessions"

    @pytest.fixture
    def session_manager(
        self,
        test_sessions_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> ClaudeSessionManager:
        """Create a session manager with test data."""
        manager = ClaudeSessionManager()
        # Monkey patch the project sessions directory to use our test data
        monkeypatch.setattr(manager, "project_sessions_dir", test_sessions_dir)
        return manager

    def test_list_and_parse_sessions(
        self,
        session_manager: ClaudeSessionManager,
    ) -> None:
        """Test listing and parsing Claude sessions."""
        sessions = session_manager.list_sessions()

        # Should find multiple sessions
        assert len(sessions) > 0, "Should find at least one session"

        # Check that sessions are sorted by last activity (most recent first)
        for i in range(1, len(sessions)):
            assert sessions[i - 1]["last_activity"] >= sessions[i]["last_activity"], (
                "Sessions should be sorted by last activity"
            )

        # Verify session structure
        for session in sessions:
            assert "session_id" in session
            assert "summary" in session
            assert "first_message" in session
            assert "message_count" in session
            assert "last_activity" in session
            assert "file_path" in session

            # Session ID should match file name
            assert session["file_path"].endswith(f"{session['session_id']}.jsonl")

            # Message count should be non-negative
            assert session["message_count"] >= 0

            # Summary and first_message should be strings
            assert isinstance(session["summary"], str)
            assert isinstance(session["first_message"], str)

        # Test getting a specific session
        if sessions:
            first_session_id = sessions[0]["session_id"]
            assert session_manager.session_exists(first_session_id)

            session_path = session_manager.get_session_file_path(first_session_id)
            assert session_path is not None
            assert session_path.exists()

        # Test non-existent session
        assert not session_manager.session_exists("non-existent-session-id")
        assert session_manager.get_session_file_path("non-existent-session-id") is None

    def test_get_session_with_messages(
        self,
        session_manager: ClaudeSessionManager,
    ) -> None:
        """Test getting a session with its messages."""
        sessions = session_manager.list_sessions()

        # Ensure we have at least one session to test
        assert len(sessions) > 0, "Need at least one session to test"

        # Get the first session with messages
        session_id = sessions[0]["session_id"]
        session_data = session_manager.get_session_with_messages(session_id)

        assert session_data is not None
        assert session_data["session_id"] == session_id
        assert "messages" in session_data

        # Verify messages structure
        messages = session_data["messages"]
        assert isinstance(messages, list)

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

        # Number of messages should match message_count
        assert len(messages) == session_data["message_count"]

    def test_get_non_existent_session_with_messages(
        self,
        session_manager: ClaudeSessionManager,
    ) -> None:
        """Test getting messages for a non-existent session."""
        session_data = session_manager.get_session_with_messages("non-existent-id")
        assert session_data is None
