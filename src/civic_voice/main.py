"""Entry point for Civic Voice AI server."""

import asyncio

from dotenv import load_dotenv

from .config.settings import Settings
from .server import CivicVoiceServer
from .repository.local import LocalQuestionSetRepository, LocalResponseRepository


def main() -> None:
    """Start the Civic Voice AI server."""
    # Load environment variables
    load_dotenv()

    # Initialize settings
    settings = Settings()

    # Initialize repositories
    data_path = settings.storage.data_path
    question_set_repo = LocalQuestionSetRepository(data_path)
    response_repo = LocalResponseRepository(data_path)

    # Create and start server
    server = CivicVoiceServer(
        settings=settings,
        question_set_repo=question_set_repo,
        response_repo=response_repo,
    )

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer shutdown.")


if __name__ == "__main__":
    main()
