"""Domain models for Civic Voice AI."""

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
    """A collection of civic duty questions."""
    id: str
    name: str
    questions: list[str]
    created_at: datetime
    active: bool = True

    def __post_init__(self):
        if len(self.questions) != 3:
            raise ValueError("QuestionSet must have exactly 3 questions")


@dataclass
class AgentResponse:
    """An agent's responses to a question set."""
    id: str
    question_set_id: str
    agent_email: str
    answers: list[bool]  # [True, False, True] for y/n/y
    completed_at: datetime

    def __post_init__(self):
        if len(self.answers) != 3:
            raise ValueError("AgentResponse must have exactly 3 answers")


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
