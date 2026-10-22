import argparse

import uvicorn

from src.config import settings


def main():
    parser = argparse.ArgumentParser(
        description="Sina Hotels AI Voice Receptionist & Room CRM (Sina Bernini Bristol)"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run FastAPI server for REST API and webhooks",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run terminal-based interactive phone call simulator",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.PORT,
        help=f"Port to bind the server to (default: {settings.PORT})",
    )

    args = parser.parse_args()

    if args.serve:
        print(f"Starting FastAPI server on http://{args.host}:{args.port}")
        uvicorn.run("src.api.main:app", host=args.host, port=args.port, reload=True)
    else:
        from src.cli import main as cli_main

        cli_main()


if __name__ == "__main__":
    main()
