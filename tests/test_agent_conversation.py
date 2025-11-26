"""Test agent conversation extraction and formatting.

Tests that _extract_sidechain() correctly formats full agent conversation
with text responses and tool operations in chronological order.
"""

import json
from pathlib import Path
import sys

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from claude_transcript import Entry, SessionProcessor


def test_extract_sidechain_formats_full_conversation():
    """Test that _extract_sidechain formats agent conversation with text and tools.

    Creates Entry objects representing an agent conversation:
    - Agent text response
    - Agent tool operations (Read, Edit)
    - More agent text
    - More tool operations

    Verifies the formatted output contains:
    - Text responses as paragraphs
    - Tool operations formatted with dashes and proper formatting
    - Chronological ordering maintained
    """
    # Create test entries representing agent conversation
    entries = [
        # Agent text response
        Entry({
            'type': 'assistant',
            'uuid': 'agent-msg-001',
            'timestamp': '2025-11-26T10:00:00Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'I will read the configuration file and update it.'
                    }
                ]
            }
        }),
        # Agent tool operations
        Entry({
            'type': 'assistant',
            'uuid': 'agent-tool-001',
            'timestamp': '2025-11-26T10:00:01Z',
            'message': {
                'content': [
                    {
                        'type': 'tool_use',
                        'name': 'Read',
                        'input': {
                            'file_path': '/home/user/config.yaml'
                        }
                    }
                ]
            }
        }),
        # Another agent text response
        Entry({
            'type': 'assistant',
            'uuid': 'agent-msg-002',
            'timestamp': '2025-11-26T10:00:02Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'Now I will update the database setting.'
                    }
                ]
            }
        }),
        # Another tool operation
        Entry({
            'type': 'assistant',
            'uuid': 'agent-tool-002',
            'timestamp': '2025-11-26T10:00:03Z',
            'message': {
                'content': [
                    {
                        'type': 'tool_use',
                        'name': 'Edit',
                        'input': {
                            'file_path': '/home/user/config.yaml',
                            'old_string': 'db_host: localhost',
                            'new_string': 'db_host: production.example.com'
                        }
                    }
                ]
            }
        }),
        # Final text response
        Entry({
            'type': 'assistant',
            'uuid': 'agent-msg-003',
            'timestamp': '2025-11-26T10:00:04Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'Configuration updated successfully.'
                    }
                ]
            }
        })
    ]

    # Create processor and call _extract_sidechain
    processor = SessionProcessor()

    # This should fail with AttributeError: 'SessionProcessor' object has no attribute '_extract_sidechain'
    result = processor._extract_sidechain(entries)

    # Verify formatted output contains expected elements
    assert isinstance(result, str)

    # Check for text content (as paragraphs)
    assert 'I will read the configuration file and update it.' in result
    assert 'Now I will update the database setting.' in result
    assert 'Configuration updated successfully.' in result

    # Check for tool operations formatted with dashes
    assert '- **Read**:' in result
    assert '`/home/user/config.yaml`' in result
    assert '- **Edit**:' in result

    # Verify chronological ordering (first text should appear before second)
    text1_pos = result.find('I will read the configuration file')
    text2_pos = result.find('Now I will update the database setting')
    text3_pos = result.find('Configuration updated successfully')

    assert text1_pos < text2_pos < text3_pos, "Text responses should appear in chronological order"
