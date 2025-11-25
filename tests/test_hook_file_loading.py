"""Test hook file discovery by transcript_path field.

Tests that SessionProcessor._find_hook_file() discovers hook JSONL files
by matching the transcript_path field in hook entries.
"""

import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def claude_transcript_module():
    """Import and return the claude_transcript module."""
    import sys
    from pathlib import Path

    # Add the project root to sys.path so we can import claude_transcript
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    import claude_transcript
    return claude_transcript


def test_find_hook_file_by_transcript_path(claude_transcript_module):
    """Test that _find_hook_file discovers hook file by transcript_path field.

    Integration test workflow:
    1. Creates a session JSONL file at specific path
    2. Creates a hook JSONL file with transcript_path pointing to session
    3. Calls _find_hook_file(session_path)
    4. Verifies it returns the hook file path

    Expected to fail with: AttributeError: 'SessionProcessor' object has no
    attribute '_find_hook_file'
    """
    # Arrange: Create temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create session file
        session_path = Path(tmpdir) / "session-abc123.jsonl"
        session_entries = [
            {
                "type": "summary",
                "uuid": "abc123",
                "content": {"summary": "Test session for hook discovery"}
            },
            {
                "type": "user",
                "uuid": "user-001",
                "timestamp": "2025-11-25T10:00:00Z",
                "message": {
                    "content": [{"type": "text", "text": "Test message"}]
                }
            }
        ]
        with open(session_path, "w", encoding="utf-8") as f:
            for entry in session_entries:
                f.write(json.dumps(entry) + "\n")

        # Create hook directory and hook file
        hook_dir = Path(tmpdir) / "hooks"
        hook_dir.mkdir()
        hook_path = hook_dir / "2025-11-25-abc123-hooks.jsonl"

        # Hook file with transcript_path pointing to session file
        hook_entries = [
            {
                "type": "hook_execution",
                "timestamp": "2025-11-25T09:55:00Z",
                "hook_name": "session_start",
                "transcript_path": str(session_path),  # Critical field for discovery
                "context": "Hook context for session abc123"
            }
        ]
        with open(hook_path, "w", encoding="utf-8") as f:
            for entry in hook_entries:
                f.write(json.dumps(entry) + "\n")

        # Act: Call _find_hook_file with session path
        processor = claude_transcript_module.SessionProcessor()
        result = processor._find_hook_file(str(session_path))

        # Assert: Should return the hook file path
        assert result == str(hook_path), (
            f"Expected _find_hook_file to return {hook_path}, got {result}"
        )


def test_find_hook_file_no_match_returns_none(claude_transcript_module):
    """Test that _find_hook_file returns None when no hook file matches.

    Edge case: Session exists but no corresponding hook file.
    """
    # Arrange: Create session file only (no hook file)
    with tempfile.TemporaryDirectory() as tmpdir:
        session_path = Path(tmpdir) / "session-xyz789.jsonl"
        session_entries = [
            {
                "type": "summary",
                "uuid": "xyz789",
                "content": {"summary": "Session without hooks"}
            }
        ]
        with open(session_path, "w", encoding="utf-8") as f:
            for entry in session_entries:
                f.write(json.dumps(entry) + "\n")

        # Act: Call _find_hook_file (no hook file exists)
        processor = claude_transcript_module.SessionProcessor()
        result = processor._find_hook_file(str(session_path))

        # Assert: Should return None
        assert result is None, (
            f"Expected None when no hook file exists, got {result}"
        )


def test_find_hook_file_multiple_hooks_returns_match(claude_transcript_module):
    """Test that _find_hook_file finds correct hook among multiple hook files.

    Edge case: Multiple hook files exist, should return only the one matching
    transcript_path.
    """
    # Arrange: Create multiple sessions and hook files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Session A
        session_a_path = Path(tmpdir) / "session-aaa111.jsonl"
        with open(session_a_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "summary",
                "uuid": "aaa111",
                "content": {"summary": "Session A"}
            }) + "\n")

        # Session B (target)
        session_b_path = Path(tmpdir) / "session-bbb222.jsonl"
        with open(session_b_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "summary",
                "uuid": "bbb222",
                "content": {"summary": "Session B"}
            }) + "\n")

        # Hook directory with multiple hook files
        hook_dir = Path(tmpdir) / "hooks"
        hook_dir.mkdir()

        # Hook for session A
        hook_a_path = hook_dir / "2025-11-25-aaa111-hooks.jsonl"
        with open(hook_a_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "hook_execution",
                "transcript_path": str(session_a_path),
                "context": "Hook for session A"
            }) + "\n")

        # Hook for session B (target)
        hook_b_path = hook_dir / "2025-11-25-bbb222-hooks.jsonl"
        with open(hook_b_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "hook_execution",
                "transcript_path": str(session_b_path),
                "context": "Hook for session B"
            }) + "\n")

        # Act: Find hook for session B
        processor = claude_transcript_module.SessionProcessor()
        result = processor._find_hook_file(str(session_b_path))

        # Assert: Should return hook B path (not hook A)
        assert result == str(hook_b_path), (
            f"Expected {hook_b_path}, got {result}. "
            "Should match transcript_path in hook file."
        )


def test_load_hook_entries_extracts_additionalContext(claude_transcript_module):
    """Test that _load_hook_entries parses hookSpecificOutput.additionalContext.

    Integration test workflow:
    1. Creates a hook JSONL file with hookSpecificOutput structure
    2. Calls _load_hook_entries(hook_file_path)
    3. Verifies it returns list of Entry objects
    4. Verifies Entry objects have correct type and additionalContext

    Expected to fail with: AttributeError: 'SessionProcessor' object has no
    attribute '_load_hook_entries'
    """
    # Arrange: Create hook file with hookSpecificOutput structure
    with tempfile.TemporaryDirectory() as tmpdir:
        hook_path = Path(tmpdir) / "test-hooks.jsonl"

        # Hook entries with hookSpecificOutput.additionalContext
        hook_entries = [
            {
                "hook_event": "UserPromptSubmit",
                "logged_at": "2025-11-25T05:39:21.115514+00:00",
                "session_id": "test-session-123",
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "**CRITICAL**: Test hook context for verification"
                }
            },
            {
                "hook_event": "SessionStart",
                "logged_at": "2025-11-25T05:38:00.000000+00:00",
                "session_id": "test-session-123",
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": "Session initialization context"
                }
            }
        ]

        with open(hook_path, "w", encoding="utf-8") as f:
            for entry in hook_entries:
                f.write(json.dumps(entry) + "\n")

        # Act: Call _load_hook_entries
        processor = claude_transcript_module.SessionProcessor()
        entries = processor._load_hook_entries(str(hook_path))

        # Assert: Should return list of Entry objects
        assert isinstance(entries, list), (
            f"Expected list of entries, got {type(entries)}"
        )
        assert len(entries) == 2, (
            f"Expected 2 entries from hook file, got {len(entries)}"
        )

        # Verify first entry structure
        first_entry = entries[0]
        assert first_entry.type == "system_reminder", (
            f"Expected entry type 'system_reminder', got {first_entry.type}"
        )
        assert "CRITICAL" in first_entry.additional_context, (
            f"Expected 'CRITICAL' in additional_context, got: {first_entry.additional_context}"
        )
        assert "Test hook context" in first_entry.additional_context, (
            "Expected full additionalContext text in entry"
        )

        # Verify timestamp extraction
        assert first_entry.timestamp is not None, (
            "Expected timestamp from logged_at field"
        )

        # Verify second entry
        second_entry = entries[1]
        assert second_entry.type == "system_reminder"
        assert "Session initialization" in second_entry.additional_context
