"""Supabase repository implementation."""

from datetime import datetime
from typing import Optional

from supabase import create_client, Client

from ..models import QuestionSet, AgentResponse
from .base import QuestionSetRepository, ResponseRepository


class SupabaseClientManager:
    """Manages Supabase client lifecycle."""

    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self._client: Optional[Client] = None

    def get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            self._client = create_client(self.url, self.key)
        return self._client


class SupabaseQuestionSetRepository(QuestionSetRepository):
    """Supabase-backed question set repository."""

    def __init__(self, client_manager: SupabaseClientManager):
        self.client_manager = client_manager

    def _to_model(self, data: dict) -> QuestionSet:
        """Convert Supabase row to QuestionSet model."""
        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return QuestionSet(
            id=data["id"],
            name=data["name"],
            q1=data["q1"],
            q2=data["q2"],
            q3=data["q3"],
            created_at=created_at,
            active=data.get("active", True),
        )

    async def get_active(self) -> Optional[QuestionSet]:
        """Get the most recently created active question set."""
        client = self.client_manager.get_client()
        response = (
            client.table("question_sets")
            .select("*")
            .eq("active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return self._to_model(response.data[0])
        return None

    async def get_by_id(self, id: str) -> Optional[QuestionSet]:
        """Get a question set by ID."""
        client = self.client_manager.get_client()
        response = client.table("question_sets").select("*").eq("id", id).limit(1).execute()
        if response.data:
            return self._to_model(response.data[0])
        return None

    async def create(self, question_set: QuestionSet) -> None:
        """Create a new question set."""
        client = self.client_manager.get_client()
        client.table("question_sets").insert({
            "id": question_set.id,
            "name": question_set.name,
            "q1": question_set.q1,
            "q2": question_set.q2,
            "q3": question_set.q3,
            "created_at": question_set.created_at.isoformat(),
            "active": question_set.active,
        }).execute()

    async def get_all(self) -> list[QuestionSet]:
        """Get all question sets."""
        client = self.client_manager.get_client()
        response = (
            client.table("question_sets")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return [self._to_model(item) for item in response.data]


class SupabaseResponseRepository(ResponseRepository):
    """Supabase-backed response repository."""

    def __init__(self, client_manager: SupabaseClientManager):
        self.client_manager = client_manager

    def _to_model(self, data: dict) -> AgentResponse:
        """Convert Supabase row to AgentResponse model."""
        completed_at = data["completed_at"]
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        return AgentResponse(
            id=data["id"],
            question_set_id=data["question_set_id"],
            agent_email=data["agent_email"],
            a1=data["a1"],
            a2=data["a2"],
            a3=data["a3"],
            completed_at=completed_at,
        )

    async def save(self, response: AgentResponse) -> None:
        """Save an agent response."""
        client = self.client_manager.get_client()
        client.table("agent_responses").insert({
            "id": response.id,
            "question_set_id": response.question_set_id,
            "agent_email": response.agent_email,
            "a1": response.a1,
            "a2": response.a2,
            "a3": response.a3,
            "completed_at": response.completed_at.isoformat(),
        }).execute()

        # Print to console
        print("\n" + "=" * 50)
        print("NEW AGENT RESPONSE RECORDED (Supabase)")
        print("=" * 50)
        print(f"Email: {response.agent_email}")
        print(f"Question Set: {response.question_set_id}")
        print(f"Answers: {['Yes' if a else 'No' for a in response.answers]}")
        print(f"Completed: {response.completed_at}")
        print("=" * 50 + "\n")

    async def get_by_email(self, email: str) -> list[AgentResponse]:
        """Get all responses from an agent by email."""
        client = self.client_manager.get_client()
        response = client.table("agent_responses").select("*").eq("agent_email", email).execute()
        return [self._to_model(item) for item in response.data]
