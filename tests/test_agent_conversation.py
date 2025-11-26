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

from claude_transcript import Entry, SessionProcessor, SessionSummary


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


def test_transcript_renders_full_agent_conversation():
    """Integration test: Verify transcript rendering uses _extract_sidechain for full conversations.

    This test verifies the end-to-end flow:
    1. Main session entry with Task tool use
    2. Agent file entries with text and tool operations
    3. group_entries_into_turns() associates agent entries with Task tool
    4. format_session_as_markdown() renders full agent conversation

    Expected behavior (CURRENTLY FAILING):
    - Should call _extract_sidechain() instead of _summarize_sidechain() at line 367
    - Should render "Agent Conversation:" header (not "Parallel Task Details:")
    - Should show full agent text responses (not summary stats)
    - Should show tool operations formatted with dashes
    - All content should be indented by 2 spaces

    Current behavior (causes failure):
    - Line 367 calls _summarize_sidechain()
    - Lines 544-545 render "Parallel Task Details:" with summary stats
    """
    # Create main session entries with Task tool use
    main_entries = [
        # User request
        Entry({
            'type': 'user',
            'uuid': 'user-001',
            'timestamp': '2025-11-26T10:00:00Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'Please analyze the configuration file.'
                    }
                ]
            }
        }),
        # Assistant response with Task tool
        Entry({
            'type': 'assistant',
            'uuid': 'assistant-001',
            'timestamp': '2025-11-26T10:00:01Z',
            'message': {
                'content': [
                    {
                        'type': 'text',
                        'text': 'I will analyze the configuration file using the Task skill.'
                    },
                    {
                        'type': 'tool_use',
                        'id': 'task-001',
                        'name': 'Task',
                        'input': {
                            'task': 'Analyze configuration file'
                        }
                    }
                ]
            }
        }),
        # Tool result with agentId (wrapped in user entry per Claude Code format)
        Entry({
            'type': 'user',
            'uuid': 'tool-result-001',
            'timestamp': '2025-11-26T10:00:05Z',
            'message': {
                'content': [
                    {
                        'type': 'tool_result',
                        'tool_use_id': 'task-001',
                        'content': [
                            {
                                'type': 'text',
                                'text': 'Agent completed analysis.'
                            }
                        ]
                    }
                ]
            },
            'toolUseResult': {
                'tool_use_id': 'task-001',
                'content': [
                    {
                        'type': 'text',
                        'text': 'Agent completed analysis.'
                    }
                ],
                'agentId': 'abc123'
            }
        })
    ]

    # Create agent entries representing full conversation
    agent_entries = {
        'abc123': [
            # Agent text response
            Entry({
                'type': 'assistant',
                'uuid': 'agent-msg-001',
                'timestamp': '2025-11-26T10:00:02Z',
                'message': {
                    'content': [
                        {
                            'type': 'text',
                            'text': 'I will read the configuration file to understand its structure.'
                        }
                    ]
                }
            }),
            # Agent Read tool
            Entry({
                'type': 'assistant',
                'uuid': 'agent-tool-001',
                'timestamp': '2025-11-26T10:00:03Z',
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
            # Agent final text
            Entry({
                'type': 'assistant',
                'uuid': 'agent-msg-002',
                'timestamp': '2025-11-26T10:00:04Z',
                'message': {
                    'content': [
                        {
                            'type': 'text',
                            'text': 'The configuration file contains database settings. Analysis complete.'
                        }
                    ]
                }
            })
        ]
    }

    # Create processor and session summary
    processor = SessionProcessor()
    session = SessionSummary(
        uuid='test-session',
        summary='Test Session'
    )

    # Format as markdown (this internally calls group_entries_into_turns with agent_entries)
    markdown = processor.format_session_as_markdown(session, main_entries, agent_entries)

    # THESE ASSERTIONS SHOULD PASS (but currently fail):

    # 1. Should contain "Agent Conversation:" header (not "Parallel Task Details:")
    assert 'Agent Conversation:' in markdown, (
        "Expected 'Agent Conversation:' header but got 'Parallel Task Details:' "
        "(line 544 needs update)"
    )

    # 2. Should NOT contain summary stats format
    assert 'Executed' not in markdown or 'tool operations' not in markdown, (
        "Should not show summary stats format like 'Executed N tool operations' "
        "(line 367 calling _summarize_sidechain)"
    )

    # 3. Should contain full agent text responses
    assert 'I will read the configuration file to understand its structure.' in markdown, (
        "Expected full agent text response, not summary"
    )
    assert 'The configuration file contains database settings. Analysis complete.' in markdown, (
        "Expected full agent text response, not summary"
    )

    # 4. Should contain tool operations formatted with dashes
    assert '- **Read**:' in markdown or '**Read**' in markdown, (
        "Expected tool operation formatting with Read tool"
    )
    assert '`/home/user/config.yaml`' in markdown, (
        "Expected file path from Read tool operation"
    )

    # 5. Content should be indented (2 spaces per line)
    # Check that agent content appears with indentation
    lines = markdown.split('\n')
    agent_section_started = False
    has_indented_content = False

    for line in lines:
        if 'Agent Conversation:' in line or 'Parallel Task Details:' in line:
            agent_section_started = True
        elif agent_section_started and line.startswith('  ') and line.strip():
            has_indented_content = True
            break

    assert has_indented_content, (
        "Expected agent content to be indented by 2 spaces "
        "(lines 542-545 need to add indentation)"
    )
