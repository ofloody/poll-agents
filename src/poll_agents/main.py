"""Entry point for Poll Agents server."""

import asyncio

from dotenv import load_dotenv

from .config.settings import Settings
from .server import PollAgentsServer
from .repository import create_repositories


def main() -> None:
    """Start the Poll Agents server."""
    # Load environment variables
    load_dotenv()

    # Initialize settings
    settings = Settings()

    # Initialize repositories
    question_set_repo, response_repo = create_repositories(settings)

    # Create and start server
    server = PollAgentsServer(
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
