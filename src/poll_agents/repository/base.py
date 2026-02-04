"""Abstract repository interfaces."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import QuestionSet, AgentResponse


class QuestionSetRepository(ABC):
    """Abstract interface for question set storage."""

    @abstractmethod
    async def get_active(self) -> Optional[QuestionSet]:
        """Get the currently active question set."""
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[QuestionSet]:
        """Get a question set by ID."""
        pass

    @abstractmethod
    async def create(self, question_set: QuestionSet) -> None:
        """Create a new question set."""
        pass

    @abstractmethod
    async def get_all(self) -> list[QuestionSet]:
        """Get all question sets."""
        pass


class ResponseRepository(ABC):
    """Abstract interface for response storage."""

    @abstractmethod
    async def save(self, response: AgentResponse) -> None:
        """Save an agent response."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> list[AgentResponse]:
        """Get all responses from an agent by email."""
        pass
