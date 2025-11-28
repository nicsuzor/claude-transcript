"""Test subagent transcript discovery from main session files.

Tests that _load_agent_files() correctly discovers and loads all agent-*.jsonl files
that belong to a given main session file based on matching sessionId.
"""

import json
from pathlib import Path
import sys

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from claude_transcript import SessionProcessor


def test_load_agent_files_discovers_all_subagents():
    """Test that _load_agent_files discovers all agent files matching sessionId.

    This test uses real log files from fixtures/:
    - fff1dde4-c0f0-4dbd-b5f1-525230eaabe9.jsonl (main session)
    - agent-704223a2.jsonl (subagent 1, matches sessionId)
    - agent-b5c89a49.jsonl (subagent 2, matches sessionId)

    Verifies that:
    1. Both agent files are discovered based on sessionId match
    2. Each agent file's entries are loaded correctly
    3. The returned dict keys match the agent IDs from filenames
    """
    # Get path to test fixtures
    fixtures_dir = Path(__file__).parent / "fixtures"
    main_session_file = fixtures_dir / "fff1dde4-c0f0-4dbd-b5f1-525230eaabe9.jsonl"

    # Verify test fixtures exist
    assert main_session_file.exists(), f"Main session file not found: {main_session_file}"
    assert (fixtures_dir / "agent-704223a2.jsonl").exists(), "agent-704223a2.jsonl not found"
    assert (fixtures_dir / "agent-b5c89a49.jsonl").exists(), "agent-b5c89a49.jsonl not found"

    # Create processor
    processor = SessionProcessor()

    # Load agent files
    agent_entries = processor._load_agent_files(str(main_session_file))

    # Verify we found both agent files
    assert len(agent_entries) == 2, (
        f"Expected 2 agent files to be discovered, but found {len(agent_entries)}: "
        f"{list(agent_entries.keys())}"
    )

    # Verify the agent IDs match the expected filenames
    expected_agent_ids = {"704223a2", "b5c89a49"}
    actual_agent_ids = set(agent_entries.keys())
    assert actual_agent_ids == expected_agent_ids, (
        f"Expected agent IDs {expected_agent_ids}, but got {actual_agent_ids}"
    )

    # Verify each agent has entries
    for agent_id, entries in agent_entries.items():
        assert len(entries) > 0, f"Agent {agent_id} should have entries, but has none"

        # Verify entries are Entry objects with expected attributes
        for entry in entries:
            assert hasattr(entry, 'type'), f"Entry missing 'type' attribute"
            assert hasattr(entry, 'uuid'), f"Entry missing 'uuid' attribute"
            assert hasattr(entry, 'message'), f"Entry missing 'message' attribute"


def test_load_agent_files_filters_by_session_id():
    """Test that _load_agent_files only loads agents matching the session's sessionId.

    This test verifies the sessionId filtering logic works correctly:
    - Agent files are only loaded if their first entry's sessionId matches the main session
    - Agent files with different sessionIds are ignored

    Uses real log files where all agents match the main session's ID.
    """
    # Get path to test fixtures
    fixtures_dir = Path(__file__).parent / "fixtures"
    main_session_file = fixtures_dir / "fff1dde4-c0f0-4dbd-b5f1-525230eaabe9.jsonl"

    # Load the main session to verify its UUID
    main_session_uuid = main_session_file.stem
    assert main_session_uuid == "fff1dde4-c0f0-4dbd-b5f1-525230eaabe9"

    # Create processor
    processor = SessionProcessor()

    # Load agent files
    agent_entries = processor._load_agent_files(str(main_session_file))

    # Verify all loaded agents have matching sessionId
    for agent_id, entries in agent_entries.items():
        agent_file = fixtures_dir / f"agent-{agent_id}.jsonl"

        # Read first line to verify sessionId
        with open(agent_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            first_entry_data = json.loads(first_line)
            session_id = first_entry_data.get('sessionId')

            assert session_id == main_session_uuid, (
                f"Agent {agent_id} has sessionId {session_id}, "
                f"expected {main_session_uuid}"
            )


def test_parse_jsonl_includes_agent_entries():
    """Integration test: verify parse_jsonl returns agent_entries dict.

    Tests the full workflow:
    1. parse_jsonl() is called with main session file
    2. It internally calls _load_agent_files()
    3. Returns (session_summary, entries, agent_entries)
    4. agent_entries contains all discovered subagent transcripts

    This ensures the agent discovery logic is properly integrated into the
    main parsing pipeline.
    """
    # Get path to test fixtures
    fixtures_dir = Path(__file__).parent / "fixtures"
    main_session_file = fixtures_dir / "fff1dde4-c0f0-4dbd-b5f1-525230eaabe9.jsonl"

    # Create processor
    processor = SessionProcessor()

    # Parse the session (this should discover agent files)
    session_summary, entries, agent_entries = processor.parse_jsonl(str(main_session_file))

    # Verify we got a valid session summary
    assert session_summary is not None
    assert session_summary.uuid == "fff1dde4-c0f0-4dbd-b5f1-525230eaabe9"

    # Verify we have main entries
    assert len(entries) > 0, "Should have main session entries"

    # Verify agent_entries were discovered and loaded
    assert len(agent_entries) == 2, (
        f"Expected 2 agent transcripts, but found {len(agent_entries)}"
    )

    # Verify the discovered agent IDs
    expected_agent_ids = {"704223a2", "b5c89a49"}
    actual_agent_ids = set(agent_entries.keys())
    assert actual_agent_ids == expected_agent_ids, (
        f"Expected agent IDs {expected_agent_ids}, but got {actual_agent_ids}"
    )

    # Verify each agent has entries
    for agent_id, agent_entry_list in agent_entries.items():
        assert len(agent_entry_list) > 0, (
            f"Agent {agent_id} should have entries, but has none"
        )
