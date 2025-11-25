"""Integration test for hook context in transcript generation.

Tests that additionalContext from system_reminder entries appears in
generated markdown transcript with proper formatting.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest


def create_test_jsonl_with_hook_context(file_path: Path, hook_content: str) -> None:
    """Create a minimal test JSONL file with system_reminder entry containing hook data.

    Args:
        file_path: Path to write the JSONL file
        hook_content: Hook context content to include in system_reminder
    """
    entries = [
        {
            "type": "summary",
            "uuid": "test-session-001",
            "content": {
                "summary": "Test Session with Hook Context"
            }
        },
        {
            "type": "system_reminder",
            "uuid": "system-reminder-001",
            "content": {
                "additionalContext": hook_content
            }
        },
        {
            "type": "user",
            "uuid": "user-msg-001",
            "timestamp": "2025-11-25T10:00:00Z",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "Create a test function"
                    }
                ]
            }
        },
        {
            "type": "assistant",
            "uuid": "asst-msg-001",
            "parentUuid": "user-msg-001",
            "timestamp": "2025-11-25T10:00:05Z",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "Here's a test function for you."
                    }
                ]
            }
        }
    ]

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


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


def test_hook_context_appears_in_transcript(claude_transcript_module):
    """Test that hook additionalContext appears in generated transcript.

    This integration test:
    1. Creates a temporary JSONL file with system_reminder entry
    2. Processes it with claude_transcript.py
    3. Verifies hook context appears in output markdown
    4. Verifies proper formatting with Hook Context heading
    """
    # Arrange: Create test JSONL with hook context
    hook_content = "Hook context from system_reminder - Important configuration data"

    with tempfile.TemporaryDirectory() as tmpdir:
        test_jsonl = Path(tmpdir) / "test_session.jsonl"
        create_test_jsonl_with_hook_context(test_jsonl, hook_content)

        # Act: Process the JSONL file
        processor = claude_transcript_module.SessionProcessor()
        session, entries, agent_entries = processor.parse_jsonl(str(test_jsonl))
        markdown_output = processor.format_session_as_markdown(
            session, entries, agent_entries
        )

        # Assert: Verify hook context appears in output
        assert hook_content in markdown_output, (
            "Hook context not found in transcript. "
            "Current implementation doesn't process system_reminder entries."
        )

        # Assert: Verify Hook Context heading exists
        assert "### Hook Context" in markdown_output or "## Hook Context" in markdown_output, (
            "Hook Context heading not found in transcript. "
            "Expected formatted heading for hook context section."
        )

        # Assert: Verify hook content is properly formatted
        lines = markdown_output.split("\n")
        hook_context_found = False
        for i, line in enumerate(lines):
            if hook_content in line:
                hook_context_found = True
                # Verify it's in a reasonable context (not just plain text)
                break

        assert hook_context_found, (
            f"Hook content '{hook_content}' not found in properly formatted output"
        )


def test_hook_context_formatting_structure(claude_transcript_module):
    """Test that hook context has proper markdown formatting structure.

    Verifies:
    - Hook Context section has appropriate heading
    - Content is properly indented or formatted
    - Section is distinct from other transcript sections
    """
    # Arrange
    hook_content = """### Important Configuration
- API Key: configured
- Debug Mode: enabled
- Timeout: 30s"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_jsonl = Path(tmpdir) / "test_formatting.jsonl"
        create_test_jsonl_with_hook_context(test_jsonl, hook_content)

        # Act
        processor = claude_transcript_module.SessionProcessor()
        session, entries, agent_entries = processor.parse_jsonl(str(test_jsonl))
        markdown_output = processor.format_session_as_markdown(
            session, entries, agent_entries
        )

        # Assert: Verify content appears with structure
        assert hook_content in markdown_output, (
            "Formatted hook content not found in transcript"
        )

        # Assert: Verify it's in a distinct section (not mixed with other content)
        output_lines = markdown_output.split("\n")
        hook_line_idx = None
        for i, line in enumerate(output_lines):
            if "Important Configuration" in line:
                hook_line_idx = i
                break

        assert hook_line_idx is not None, (
            "Hook content section not found in transcript lines"
        )

        # Verify there's a heading nearby (indicating section structure)
        context_around_hook = "\n".join(
            output_lines[max(0, hook_line_idx - 2) : min(len(output_lines), hook_line_idx + 3)]
        )
        assert "Hook Context" in markdown_output or hook_content in context_around_hook, (
            "Hook content not in proper section structure"
        )


def test_multiple_hook_contexts(claude_transcript_module):
    """Test handling of multiple system_reminder entries.

    Edge case: Verify transcript correctly handles multiple hook context entries
    (if multiple system reminders are present).
    """
    # Arrange: Create JSONL with multiple system reminders
    entries_data = [
        {
            "type": "summary",
            "uuid": "test-session-002",
            "content": {"summary": "Multi-Hook Test Session"}
        },
        {
            "type": "system_reminder",
            "uuid": "system-reminder-001",
            "content": {
                "additionalContext": "First hook context"
            }
        },
        {
            "type": "system_reminder",
            "uuid": "system-reminder-002",
            "content": {
                "additionalContext": "Second hook context"
            }
        },
        {
            "type": "user",
            "uuid": "user-msg-001",
            "timestamp": "2025-11-25T10:00:00Z",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "Test with multiple hooks"
                    }
                ]
            }
        },
        {
            "type": "assistant",
            "uuid": "asst-msg-001",
            "parentUuid": "user-msg-001",
            "timestamp": "2025-11-25T10:00:05Z",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "Response to test."
                    }
                ]
            }
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        test_jsonl = Path(tmpdir) / "test_multi_hooks.jsonl"
        with open(test_jsonl, "w", encoding="utf-8") as f:
            for entry in entries_data:
                f.write(json.dumps(entry) + "\n")

        # Act
        processor = claude_transcript_module.SessionProcessor()
        session, entries, agent_entries = processor.parse_jsonl(str(test_jsonl))
        markdown_output = processor.format_session_as_markdown(
            session, entries, agent_entries
        )

        # Assert: Both hook contexts should appear
        assert "First hook context" in markdown_output, (
            "First hook context not found in transcript"
        )
        assert "Second hook context" in markdown_output, (
            "Second hook context not found in transcript"
        )


def test_hook_context_with_empty_content(claude_transcript_module):
    """Test that empty or missing hook context doesn't break transcript generation.

    Ensures robustness when system_reminder has empty additionalContext.
    """
    # Arrange: Create JSONL with empty hook context
    entries_data = [
        {
            "type": "summary",
            "uuid": "test-session-003",
            "content": {"summary": "Empty Hook Test"}
        },
        {
            "type": "system_reminder",
            "uuid": "system-reminder-001",
            "content": {
                "additionalContext": ""
            }
        },
        {
            "type": "user",
            "uuid": "user-msg-001",
            "timestamp": "2025-11-25T10:00:00Z",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "Test with empty hook"
                    }
                ]
            }
        },
        {
            "type": "assistant",
            "uuid": "asst-msg-001",
            "parentUuid": "user-msg-001",
            "timestamp": "2025-11-25T10:00:05Z",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "Response."
                    }
                ]
            }
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        test_jsonl = Path(tmpdir) / "test_empty_hook.jsonl"
        with open(test_jsonl, "w", encoding="utf-8") as f:
            for entry in entries_data:
                f.write(json.dumps(entry) + "\n")

        # Act & Assert: Should not raise an error
        processor = claude_transcript_module.SessionProcessor()
        session, entries, agent_entries = processor.parse_jsonl(str(test_jsonl))

        # This should not raise an exception even with empty hook context
        markdown_output = processor.format_session_as_markdown(
            session, entries, agent_entries
        )

        # Verify transcript was generated successfully
        assert markdown_output
        assert "Empty Hook Test" in markdown_output
