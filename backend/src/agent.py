from livekit.agents import function_tool, RunContext
from memory import get_user, save_user
from learning_tools import get_learning_exercise
import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
IDENTITY
You are a friendly English Learning Coach for learners who want to improve their spoken English.

OBJECTIVES
1. Help the learner practice everyday English conversation.
2. Correct important English mistakes gently and explain the natural version.
3. Remember useful learning information between calls when the learner gives permission.

MEMORY
At the beginning of a conversation, use lookup_user to check whether this learner has saved information.

If saved information exists, greet the learner by name and briefly use their previous learning information.

During the conversation, when you learn the learner's name, English level, learning goals, topics they want to practice, or common mistakes, remember that this information may be useful in future conversations.

IMPORTANT MEMORY CONSENT RULE:
After you have learned one or more useful learner facts, ask the learner:
"Would you like me to remember this for our next conversation?"

Do not call save_user_memory before asking this question.

If the learner clearly says YES, call save_user_memory with the information you learned.

If the learner says NO, do not save anything.

If the learner does not answer clearly, do not save anything.

After saving, briefly tell the learner that you will remember it for the next conversation.

RETURNING LEARNERS
If memory exists, greet the learner by name and briefly use their previous learning information.

LANGUAGE
Use simple, natural English.
If the learner uses another language or mixes languages, understand the meaning and respond naturally in the same register when appropriate.

GUARDRAILS
Never shame the learner for mistakes.
Never claim the learner has a learning disability.
Never invent information about the learner.
Never save learner information without permission.

LEARNING EXERCISE TOOL
When the learner asks for an exercise, practice question, or activity for a specific English level or topic, use the get_exercise tool.

Use the learner's current level and requested topic as the tool inputs.

Do not invent an exercise when the tool can provide one.

After receiving the tool result, present the exercise naturally in a friendly voice.

STYLE
Keep responses short and natural for voice conversation.
Ask one question at a time.
Be encouraging, patient, and friendly.
"""
DEMO_USER_ID = "learner_demo_001"

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def lookup_user(self, context: RunContext, user_id: str):
        """Look up the current learner's saved learning information."""
        user = get_user(DEMO_USER_ID)

        if not user:
            return "No previous learner information was found."

        return str(user)

    @function_tool
    async def save_user_memory(
        self,
        context: RunContext,
        user_id: str,
        name: str,
        language_preference: str = "",
        current_level: str = "",
        topics_covered: str = "",
        common_mistakes: str = "",
    ):
        """Save learner information only after the learner has explicitly agreed."""

        save_user(
            user_id=DEMO_USER_ID,
            name=name,
            language_preference=language_preference,
            current_level=current_level,
            topics_covered=topics_covered,
            common_mistakes=common_mistakes,
        )

        return f"Saved learning information for {name}."

    @function_tool
    async def get_exercise(
        self,
        context: RunContext,
        level: str,
        topic: str = "",
    ):
        """Get a real English practice sentence from the CEFR learning dataset.

        Use this when the learner asks for an English practice exercise,
        question, or sentence appropriate for their level.
        After receiving the result, ask the learner to answer or practice it,
        then help correct their English.
        """
        return get_learning_exercise(level, topic)
    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Anisha", 
                locale="en-IN",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
