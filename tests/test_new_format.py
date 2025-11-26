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


def test_timing_format_as_bullet_list():
    """Test that timing information is formatted as bullet list.

    Currently timing is formatted as: "Offset: +< 1 second · Duration: < 1 second"
    Expected new format: bullet list with asterisks:
    * Offset: +< 1 second
    * Duration: < 1 second

    This test should FAIL because the current implementation uses " · " separator
    instead of bullet list format.
    """
    # Create entries for two turns so second turn has offset timing
    entries = [
        # Turn 1: User message
        Entry({
            'type': 'user',
            'uuid': 'user-msg-001',
            'timestamp': '2025-11-26T10:00:00Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'First question'
                    }
                ]
            }
        }),
        # Turn 1: Assistant response
        Entry({
            'type': 'assistant',
            'uuid': 'agent-msg-001',
            'timestamp': '2025-11-26T10:00:01Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'First answer'
                    }
                ]
            }
        }),
        # Turn 2: User message (will have offset from turn 1)
        Entry({
            'type': 'user',
            'uuid': 'user-msg-002',
            'timestamp': '2025-11-26T10:00:05Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'Second question'
                    }
                ]
            }
        }),
        # Turn 2: Assistant response
        Entry({
            'type': 'assistant',
            'uuid': 'agent-msg-002',
            'timestamp': '2025-11-26T10:00:06Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'Second answer'
                    }
                ]
            }
        })
    ]

    # Create processor
    processor = SessionProcessor()

    # Group entries into turns
    turns = processor.group_entries_into_turns(entries)

    # Should have created two turns
    assert len(turns) == 2, f"Expected 2 turns, got {len(turns)}"

    # Create a session summary
    session = SessionSummary(uuid='test-session', summary='Test Session')

    # Format as markdown
    markdown = processor.format_session_as_markdown(session, entries)

    # Verify new format: timing should appear as bullet list with asterisks
    # Expected pattern in markdown:
    # * Offset: +< 1 second
    # * Duration: < 1 second
    assert "* Offset:" in markdown, \
        f"Expected markdown to contain '* Offset:' in bullet format, but got:\n{markdown}"

    assert "* Duration:" in markdown, \
        f"Expected markdown to contain '* Duration:' in bullet format, but got:\n{markdown}"

    # Verify old format (with " · " separator) is NOT used
    # The current implementation will fail this because it uses " · "
    assert " · " not in markdown or "Offset:" not in markdown, \
        f"Timing should NOT use ' · ' separator format, should use bullets instead. Got:\n{markdown}"
