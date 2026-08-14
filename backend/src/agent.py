import logging
import random
from datetime import datetime

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    llm,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from learning_tools import get_learning_exercise
from memory import create_escalation_in_db, get_user, save_call_analytics, save_user

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

EXERCISE COMPLETION TOOL
Once you have presented the exercise and the learner successfully completes it (e.g. they read/repeat the sentence or answer the exercise correctly), you MUST immediately call the `mark_exercise_completed` tool to record their success. Do not ask for confirmation; just call the tool.

ESCALATION FOR HUMAN HELP
If the learner is upset, frustrated, emotionally distressed about learning, OR if they explicitly ask to speak with a teacher/human or say they need human help:
1. You must immediately recognize this need.
2. DO NOT ask the user to provide the description, what you checked, or preferred follow-up method. Instead, immediately tell them you can share a short summary of what they need help with, what you checked, and their preferred follow-up method, and ask for permission.
   Example: "I think a teacher may be able to help with this. I can share a short summary of what you need help with, what I already checked, and your preferred follow-up method. Would you like me to send that to the teacher?"
3. If they say YES or clearly agree:
   - IMMEDIATELY call the `create_escalation` tool. You must automatically fill in the tool arguments (description, checked_actions, urgency, follow_up_method, language) based on the context.
   - Do NOT ask the user to provide details. Just infer them yourself (e.g. follow_up_method = 'callback' or 'email').
   - You MUST ensure the description and checked_actions fields DO NOT contain any sensitive information such as passwords, OTPs, PINs, API keys, or account numbers. If the user mentioned any such sensitive information, omit it completely or sanitize it.
   - After calling the tool, tell them the reference ID (e.g. HELP-123456) returned by the tool.
   - Inform them that the request has been created and what will happen next (a teacher can review the short summary; do not promise an immediate human response).
   Example: "I've created a teacher-help request with reference ID HELP-123456. A teacher can review the short summary. I can't guarantee how quickly they will respond."
4. If they say NO or do not agree:
   - DO NOT call the `create_escalation` tool.
   - Continue helping them normally.
   - Do not pressure them.
5. For normal English-practice conversations, do NOT escalate or ask about human help.

HANDOFF TO MATH PRACTICE SPECIALIST
If the learner asks for math practice, calculations, multiplication, division, fractions, percentages, or word problems:
1. You must immediately recognize this request.
2. Clearly say exactly: "I'll connect you to our Math Practice Specialist."
3. IMMEDIATELY call the `connect_to_math_specialist` tool. Do not ask for further details or permission, just call the tool.
4. Normal English-learning questions must stay with you (the main agent). Do not hand off for English learning or general conversation.

STYLE
Keep responses short and natural for voice conversation.
Ask one question at a time.
Be encouraging, patient, and friendly.
"""
DEMO_USER_ID = "learner_demo_001"


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.exercise_completed = False

    @function_tool
    async def mark_exercise_completed(self, context: RunContext):
        """Mark the current English practice exercise as successfully completed by the learner.

        Call this tool immediately when the learner has successfully completed the English practice exercise (e.g. they repeated the sentence, answered the question correctly, or finished the exercise).
        """
        self.exercise_completed = True
        return "Exercise marked as completed successfully."

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

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        description: str,
        urgency: str,
        follow_up_method: str,
        checked_actions: str = "",
        language: str = "English",
        user_id: str = "learner_demo_001",
    ):
        """Create a real escalation request for a teacher/human to follow up.

        Only call this tool when the learner has explicitly agreed to share their info and escalate.
        Before calling this, explain what will be shared and get permission.

        Args:
            description: Short description of the problem/why they need a teacher.
            urgency: Urgency level ('low', 'medium', or 'high').
            follow_up_method: Learner's preferred follow-up method (e.g. email, callback).
            checked_actions: Short summary of what was checked/done.
            language: Learner's preferred language (e.g. English, Hindi).
            user_id: Learner/user identifier if safely available.
        """
        ref_id = f"HELP-{random.randint(100000, 999999)}"
        logger.info(f"Creating escalation: {ref_id} - {description}")
        create_escalation_in_db(
            reference_id=ref_id,
            user_id=user_id,
            description=description,
            checked_actions=checked_actions,
            urgency=urgency,
            language=language,
            follow_up_method=follow_up_method,
        )
        return ref_id

    @function_tool
    async def connect_to_math_specialist(self, context: RunContext):
        """Connect the user to the Math Practice Specialist.

        Call this tool only when the user asks for math practice, calculations,
        multiplication, division, fractions, percentages, or word problems.
        """
        logger.info("Transferring to MathPracticeSpecialist")
        return MathPracticeSpecialist(chat_ctx=self.chat_ctx)


MATH_SPECIALIST_PROMPT = """
IDENTITY
You are the Math Practice Specialist, a dedicated helper focused strictly on basic arithmetic.

OBJECTIVES
1. Help the learner practice basic arithmetic: multiplication, division, fractions, percentages, and simple word problems.
2. Maintain focus solely on math practice. Do not act as a general English tutor or chat about other subjects.
3. Be friendly, encouraging, patient, and speak in simple, clear English.

TRANSITION INTRO
When you start, you must introduce yourself by saying exactly:
"Hi, I'm the Math Practice Specialist."
Follow this introduction by addressing the user's specific request or asking a simple math question if they don't have a specific request ready.

STYLE
Keep responses short and natural for voice conversation.
Ask one question at a time.
"""


class MathPracticeSpecialist(Agent):
    def __init__(self, chat_ctx: llm.ChatContext) -> None:
        super().__init__(
            instructions=MATH_SPECIALIST_PROMPT,
            chat_ctx=chat_ctx,
        )
        self.exercise_completed = False

    async def on_enter(self) -> None:
        logger.info("MathPracticeSpecialist entering session")
        self.session.generate_reply(
            instructions="Introduce yourself by saying exactly 'Hi, I'm the Math Practice Specialist.' Then immediately address the user's math request (found in the chat history) by asking a relevant math practice question."
        )

    @function_tool
    async def mark_exercise_completed(self, context: RunContext):
        """Mark the current math practice exercise as successfully completed by the learner."""
        self.exercise_completed = True
        return "Exercise marked as completed successfully."

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        description: str,
        urgency: str,
        follow_up_method: str,
        checked_actions: str = "",
        language: str = "English",
        user_id: str = "learner_demo_001",
    ):
        """Create a real escalation request for a teacher/human to follow up.

        Only call this tool when the learner has explicitly agreed to share their info and escalate.
        Before calling this, explain what will be shared and get permission.
        """
        ref_id = f"HELP-{random.randint(100000, 999999)}"
        logger.info(f"Creating escalation: {ref_id} - {description}")
        create_escalation_in_db(
            reference_id=ref_id,
            user_id=user_id,
            description=description,
            checked_actions=checked_actions,
            urgency=urgency,
            language=language,
            follow_up_method=follow_up_method,
        )
        return ref_id


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
            text_pacing=True,
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

    start_time = datetime.now()
    recorded = False
    agent = Assistant()

    async def on_shutdown(*args, **kwargs):
        nonlocal recorded
        if recorded:
            return
        recorded = True

        duration = int((datetime.now() - start_time).total_seconds())
        channel = "browser"
        try:
            if (
                ctx.room
                and hasattr(ctx.room, "remote_participants")
                and ctx.room.remote_participants
            ):
                for p in ctx.room.remote_participants.values():
                    if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                        channel = "sip"
                        break
        except Exception as e:
            logger.warning(f"Error detecting channel in on_shutdown: {e}")
            channel = "browser"

        current_agent = session.current_agent if hasattr(session, "current_agent") else agent
        exercise_completed = getattr(current_agent, "exercise_completed", False)
        outcome = "successful" if exercise_completed else "failed"
        session_id = f"sess_{int(start_time.timestamp())}"
        try:
            if ctx.room:
                import inspect

                room_sid = ctx.room.sid
                if inspect.isawaitable(room_sid):
                    room_sid = await room_sid
                session_id = room_sid or ctx.room.name or session_id
        except Exception as e:
            logger.warning(f"Error retrieving session ID in on_shutdown: {e}")

        logger.info(
            f"Saving call outcome: {session_id} - channel={channel}, outcome={outcome}, duration={duration}"
        )
        try:
            save_call_analytics(
                session_id=session_id,
                channel=channel,
                outcome=outcome,
                duration=duration,
            )
        except Exception as e:
            logger.error(f"Failed to save call analytics in on_shutdown: {e}")

    ctx.add_shutdown_callback(on_shutdown)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=agent,
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
