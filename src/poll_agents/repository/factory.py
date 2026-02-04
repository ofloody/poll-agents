"""Repository factory."""

from typing import Tuple

from ..config.settings import Settings
from .base import QuestionSetRepository, ResponseRepository
from .supabase import (
    SupabaseClientManager,
    SupabaseQuestionSetRepository,
    SupabaseResponseRepository,
)


def create_repositories(settings: Settings) -> Tuple[QuestionSetRepository, ResponseRepository]:
    """Create Supabase repositories.

    Args:
        settings: Application settings

    Returns:
        Tuple of (question_set_repo, response_repo)

    Raises:
        ValueError: If Supabase is not configured
    """
    if not settings.supabase.is_configured:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment"
        )

    client_manager = SupabaseClientManager(
        settings.supabase.url,
        settings.supabase.key,
    )
    return (
        SupabaseQuestionSetRepository(client_manager),
        SupabaseResponseRepository(client_manager),
    )
