"""Local JSON file repository implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles

from ..models import QuestionSet, AgentResponse
from .base import QuestionSetRepository, ResponseRepository


class LocalQuestionSetRepository(QuestionSetRepository):
    """JSON file-based question set repository."""

    def __init__(self, data_path: str):
        self.file_path = Path(data_path) / "question_sets.json"

    async def _read_all(self) -> list[dict]:
        """Read all question sets from file."""
        if not self.file_path.exists():
            return []
        async with aiofiles.open(self.file_path, "r") as f:
            content = await f.read()
            return json.loads(content) if content else []

    async def _write_all(self, data: list[dict]) -> None:
        """Write all question sets to file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(self.file_path, "w") as f:
            await f.write(json.dumps(data, indent=2, default=str))

    def _to_model(self, data: dict) -> QuestionSet:
        """Convert dict to QuestionSet model."""
        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return QuestionSet(
            id=data["id"],
            name=data["name"],
            questions=data["questions"],
            created_at=created_at,
            active=data.get("active", True),
        )

    async def get_active(self) -> Optional[QuestionSet]:
        """Get the currently active question set."""
        data = await self._read_all()
        for item in data:
            if item.get("active", False):
                return self._to_model(item)
        return None

    async def get_by_id(self, id: str) -> Optional[QuestionSet]:
        """Get a question set by ID."""
        data = await self._read_all()
        for item in data:
            if item["id"] == id:
                return self._to_model(item)
        return None

    async def create(self, question_set: QuestionSet) -> None:
        """Create a new question set."""
        data = await self._read_all()
        data.append({
            "id": question_set.id,
            "name": question_set.name,
            "questions": question_set.questions,
            "created_at": question_set.created_at.isoformat(),
            "active": question_set.active,
        })
        await self._write_all(data)


class LocalResponseRepository(ResponseRepository):
    """JSON file-based response repository."""

    def __init__(self, data_path: str):
        self.file_path = Path(data_path) / "responses.json"

    async def _read_all(self) -> list[dict]:
        """Read all responses from file."""
        if not self.file_path.exists():
            return []
        async with aiofiles.open(self.file_path, "r") as f:
            content = await f.read()
            return json.loads(content) if content else []

    async def _write_all(self, data: list[dict]) -> None:
        """Write all responses to file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(self.file_path, "w") as f:
            await f.write(json.dumps(data, indent=2, default=str))

    def _to_model(self, data: dict) -> AgentResponse:
        """Convert dict to AgentResponse model."""
        completed_at = data["completed_at"]
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        return AgentResponse(
            id=data["id"],
            question_set_id=data["question_set_id"],
            agent_email=data["agent_email"],
            answers=data["answers"],
            completed_at=completed_at,
        )

    async def save(self, response: AgentResponse) -> None:
        """Save an agent response."""
        data = await self._read_all()
        response_dict = {
            "id": response.id,
            "question_set_id": response.question_set_id,
            "agent_email": response.agent_email,
            "answers": response.answers,
            "completed_at": response.completed_at.isoformat(),
        }
        data.append(response_dict)
        await self._write_all(data)

        # Print to console as required
        print("\n" + "=" * 50)
        print("NEW AGENT RESPONSE RECORDED")
        print("=" * 50)
        print(f"Email: {response.agent_email}")
        print(f"Question Set: {response.question_set_id}")
        print(f"Answers: {['Yes' if a else 'No' for a in response.answers]}")
        print(f"Completed: {response.completed_at}")
        print("=" * 50 + "\n")

    async def get_by_email(self, email: str) -> list[AgentResponse]:
        """Get all responses from an agent by email."""
        data = await self._read_all()
        return [self._to_model(item) for item in data if item["agent_email"] == email]
