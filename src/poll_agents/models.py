"""Domain models for Poll Agents."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class ConversationState(Enum):
    """States in the conversation flow."""
    WELCOME = auto()
    AWAITING_EMAIL = auto()
    AWAITING_VERIFICATION = auto()
    ASKING_QUESTION_1 = auto()
    ASKING_QUESTION_2 = auto()
    ASKING_QUESTION_3 = auto()
    COMPLETED = auto()
    DISCONNECTED = auto()


@dataclass
class QuestionSet:
    """A collection of survey questions."""
    id: str
    name: str
    q1: str
    q2: str
    q3: str
    created_at: datetime
    active: bool = True

    @property
    def questions(self) -> list[str]:
        """List access for compatibility."""
        return [self.q1, self.q2, self.q3]


@dataclass
class AgentResponse:
    """An agent's responses to a question set."""
    id: str
    question_set_id: str
    agent_email: str
    a1: bool
    a2: bool
    a3: bool
    completed_at: datetime

    @property
    def answers(self) -> list[bool]:
        """List access for compatibility."""
        return [self.a1, self.a2, self.a3]


@dataclass
class AgentSession:
    """Runtime session state for an agent (not persisted)."""
    session_id: str
    state: ConversationState = ConversationState.WELCOME
    email: Optional[str] = None
    verification_code: Optional[str] = None
    verification_code_created: Optional[datetime] = None
    verification_attempts: int = 0
    question_set: Optional[QuestionSet] = None
    answers: dict[int, bool] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
