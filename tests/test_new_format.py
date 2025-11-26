"""Test turn header formatting with blank line.

Tests that turn headers are formatted as "## Turn N \n\n" (with blank line after).
"""

import json
from pathlib import Path
import sys
from datetime import datetime

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from claude_transcript import Entry, SessionProcessor, SessionSummary, ConversationTurn


def test_turn_header_includes_blank_line():
    """Test that turn header is formatted as '## Turn N \\n\\n' with blank line.

    Currently the format is '## Turn N\\n\\n' (no space before \\n\\n).
    This test verifies the new format should have a space: '## Turn N \\n\\n'.

    Creates a minimal conversation turn and renders it to markdown via
    format_session_as_markdown, verifying the turn header contains the proper spacing.
    """
    # Create minimal entries for a conversation turn
    entries = [
        Entry({
            'type': 'user',
            'uuid': 'user-msg-001',
            'timestamp': '2025-11-26T10:00:00Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'Hello'
                    }
                ]
            }
        }),
        Entry({
            'type': 'assistant',
            'uuid': 'agent-msg-001',
            'timestamp': '2025-11-26T10:00:01Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'Hi there'
                    }
                ]
            }
        })
    ]

    # Create processor
    processor = SessionProcessor()

    # Group entries into turns
    turns = processor.group_entries_into_turns(entries)

    # Should have created one turn
    assert len(turns) == 1, f"Expected 1 turn, got {len(turns)}"

    # Create a session summary
    session = SessionSummary(uuid='test-session', summary='Test Session')

    # Format as markdown
    markdown = processor.format_session_as_markdown(session, entries)

    # Verify that turn header is formatted with space before newlines
    # The header line should be "## Turn 1 " followed by newline (the space is before the newline)
    # Check for the pattern: "## Turn 1 \n\n" (with space)
    expected_header = "## Turn 1 \n\n"
    assert expected_header in markdown, \
        f"Expected markdown to contain {repr(expected_header)} but got:\n{repr(markdown[:100])}"

    # Verify current (wrong) format is NOT in the markdown
    wrong_header = "## Turn 1\n\n"
    # This assertion should FAIL initially since the code uses the wrong format
    assert wrong_header not in markdown, \
        f"Turn header should NOT be in the old format without space: {repr(wrong_header)}"
