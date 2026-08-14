import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant, MathPracticeSpecialist


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.mark.asyncio
async def test_english_request_stays_with_main() -> None:
    """Verify that a normal English practice request stays with the main agent and does not hand off."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        result = await session.run(user_input="Can you help me practice English conversation?")
        
        # Expect next event is message, not handoff
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="Coaches the user on English without handing off or connecting to math specialist.",
            )
        )
        # Verify the current agent is still Assistant
        assert isinstance(session.current_agent, Assistant)


@pytest.mark.asyncio
async def test_math_request_triggers_handoff() -> None:
    """Verify that a math request triggers a handoff, the specialist introduces itself, and context is preserved."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # The user asks for multiplication practice
        result = await session.run(user_input="Can you help me with multiplication?")
        
        # 1. Expect main agent to announce handoff
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="Announces that they are connecting the user to the Math Practice Specialist.",
            )
        )
        
        # 2. Expect the handoff tool call to execute
        result.expect.next_event().is_function_call(name="connect_to_math_specialist")
        result.expect.next_event().is_function_call_output()
        
        # 3. Expect the agent handoff event
        result.expect.next_event().is_agent_handoff(new_agent_type=MathPracticeSpecialist)

        # 4. Verify that the agent changed to MathPracticeSpecialist
        assert isinstance(session.current_agent, MathPracticeSpecialist)
        
        # 5. Expect the MathPracticeSpecialist to introduce itself and start multiplication practice
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Introduces itself exactly as 'Hi, I'm the Math Practice Specialist.'
                And then immediately asks a math practice question or starts math practice based on the context (multiplication).
                """,
            )
        )
