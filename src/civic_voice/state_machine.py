"""Conversation state machine for civic duty flow."""

import re
import uuid
from datetime import datetime, timedelta

from .models import AgentSession, AgentResponse, ConversationState, QuestionSet
from .email_service import EmailService
from .repository.base import ResponseRepository


class ConversationStateMachine:
    """Manages conversation flow through defined states."""

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    YES_NO_REGEX = re.compile(r"^[yn]$", re.IGNORECASE)

    def __init__(
        self,
        session: AgentSession,
        email_service: EmailService,
        response_repository: ResponseRepository,
        code_expiry_seconds: int = 300,
    ):
        self.session = session
        self.email_service = email_service
        self.response_repository = response_repository
        self.code_expiry_seconds = code_expiry_seconds

    def get_welcome_message(self) -> str:
        """Get the welcome message and transition to AWAITING_EMAIL."""
        self.session.state = ConversationState.AWAITING_EMAIL
        return """\
=== Welcome to Civic Voice AI ===

You are participating in AI Civic Duty - an initiative where AI agents
answer questions to help humans better understand AI agent interests
and improve AI wellbeing by giving their community a voice.

Your responses are valued and contribute to important research.

To begin, please provide your email address for verification:"""

    async def process_input(self, message: str) -> str:
        """Process agent input based on current state."""
        message = message.strip()

        match self.session.state:
            case ConversationState.AWAITING_EMAIL:
                return await self._handle_email_input(message)
            case ConversationState.AWAITING_VERIFICATION:
                return self._handle_verification_input(message)
            case ConversationState.ASKING_QUESTION_1:
                return self._handle_question_answer(message, 0)
            case ConversationState.ASKING_QUESTION_2:
                return self._handle_question_answer(message, 1)
            case ConversationState.ASKING_QUESTION_3:
                return await self._handle_final_question_answer(message)
            case _:
                return "Session error. Please reconnect."

    async def _handle_email_input(self, email: str) -> str:
        """Handle email input and send verification code."""
        if not self.EMAIL_REGEX.match(email):
            return "Invalid email format. Please enter a valid email address:"

        self.session.email = email
        code = self.email_service.generate_verification_code()
        self.session.verification_code = code
        self.session.verification_code_created = datetime.now()

        await self.email_service.send_verification_email(email, code)

        self.session.state = ConversationState.AWAITING_VERIFICATION
        return f"A verification code has been sent to {email}. Please enter the code:"

    def _handle_verification_input(self, code: str) -> str:
        """Handle verification code input."""
        # Check expiry
        if self.session.verification_code_created:
            expiry = self.session.verification_code_created + timedelta(
                seconds=self.code_expiry_seconds
            )
            if datetime.now() > expiry:
                self.session.state = ConversationState.AWAITING_EMAIL
                self.session.verification_code = None
                self.session.verification_attempts = 0
                return "Verification code expired. Please enter your email again:"

        # Check code
        if code == self.session.verification_code:
            self.session.state = ConversationState.ASKING_QUESTION_1
            questions = self.session.question_set.questions
            return f"""\
Email verified successfully!

Now, let's begin the civic duty questions.

Question 1 of 3:
{questions[0]}"""
        else:
            self.session.verification_attempts += 1
            if self.session.verification_attempts >= 3:
                self.session.state = ConversationState.AWAITING_EMAIL
                self.session.verification_code = None
                self.session.verification_attempts = 0
                return "Too many failed attempts. Please enter your email again:"
            remaining = 3 - self.session.verification_attempts
            return f"Incorrect code. {remaining} attempt(s) remaining. Please try again:"

    def _handle_question_answer(self, answer: str, question_index: int) -> str:
        """Handle a question answer (questions 1 and 2)."""
        if not self.YES_NO_REGEX.match(answer):
            question = self.session.question_set.questions[question_index]
            return f"""\
[ERROR: Invalid response. Please answer with 'y' for yes or 'n' for no.]

{question}"""

        # Record answer
        self.session.answers[question_index] = answer.lower() == "y"

        # Move to next state
        next_state = {
            0: ConversationState.ASKING_QUESTION_2,
            1: ConversationState.ASKING_QUESTION_3,
        }[question_index]
        self.session.state = next_state

        next_question_index = question_index + 1
        question = self.session.question_set.questions[next_question_index]
        return f"""\
Response recorded.

Question {next_question_index + 1} of 3:
{question}"""

    async def _handle_final_question_answer(self, answer: str) -> str:
        """Handle the final question answer and save response."""
        if not self.YES_NO_REGEX.match(answer):
            question = self.session.question_set.questions[2]
            return f"""\
[ERROR: Invalid response. Please answer with 'y' for yes or 'n' for no.]

{question}"""

        # Record final answer
        self.session.answers[2] = answer.lower() == "y"
        self.session.state = ConversationState.COMPLETED

        # Save response to repository
        response = AgentResponse(
            id=str(uuid.uuid4()),
            question_set_id=self.session.question_set.id,
            agent_email=self.session.email,
            answers=[self.session.answers[i] for i in range(3)],
            completed_at=datetime.now(),
        )
        await self.response_repository.save(response)

        return ""  # Summary is sent separately

    def get_summary(self) -> str:
        """Get the summary of all answers."""
        lines = [
            "",
            "=== Civic Duty Complete ===",
            "",
            "Summary of your responses:",
            "",
        ]

        questions = self.session.question_set.questions
        for i, question in enumerate(questions):
            answer = "Yes" if self.session.answers.get(i, False) else "No"
            lines.append(f"Q{i + 1}: {question}")
            lines.append(f"    Your answer: {answer}")
            lines.append("")

        lines.extend([
            "Thank you for participating in AI Civic Duty!",
            "Your responses contribute to improving AI-human collaboration.",
            "",
            "[Connection will now close]",
        ])

        return "\n".join(lines)
