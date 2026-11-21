import pytest

pytest.importorskip("google.adk")

from adk_agent.agent import INSTRUCTIONS, root_agent
from app.config import MODEL


def test_adk_agent_uses_the_same_model_and_instructions():
    assert root_agent.name == "aie_learning_agent"
    assert root_agent.model == MODEL
    assert root_agent.instruction == INSTRUCTIONS


def test_adk_agent_registers_the_existing_tools():
    registered = {tool.__name__ for tool in root_agent.tools}
    assert registered == {"search_glossary", "get_lecture_summary", "make_quiz"}