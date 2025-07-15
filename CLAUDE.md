# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

RAGpile is a personal assistant, a web app that you can hook your tools like email, calendar, etc. It can schedule daily tasks and can give you heads up.
It has a graph knowledge base on the user to provide relevant answers. The communication with the user happens through a telegram bot.
RAGpile is a full-stack application with three main components:
1. **Backend**: FastAPI application with SQLAlchemy, OpenAI integration, and Telegram bot. The backend uses LangGraph for agent workflows and LangChain for LLM interactions, with PostgreSQL checkpointing for conversation state persistence.
2. **Frontend**: React/TypeScript application using Vite, Tailwind CSS. Used only for admin, like setting up tokens and credentials.
3. **Telegram**: Telegram bot is the client facing app, the tool that handles communication with the user.
4. **Postgres**: Postgres is used to store the user info, e.g. tokens for various tools. It is also used to store short memory for conversations, via langgraph. It is also used as a backend for apscheduler, a tool to run dynamic scheduled tasks.
5. **Neo4j**: Neo4j is used to store the graph knowledge base.


### Docker Development
```bash
docker-compose up -d   # Start all services
docker-compose logs backend  # View backend logs
docker-compose down    # Stop all services
```

## Key File Locations

- **Backend main app**: `backend/src/app.py`
- **Database models**: `backend/src/models.py`
- **API routes**: `backend/src/auth/router.py`, `backend/src/openai_wrapper.py`
- **Telegram bot**: `backend/src/telegram_bot/application.py`
- **Email agent**: `backend/src/agents/email.py`
- **Frontend main app**: `frontend/src/App.tsx`
- **API client**: `frontend/src/lib/api.ts`
- **UI components**: `frontend/src/components/ui/`

## Development Environment

The application requires these environment variables:
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: Google OAuth credentials
- `TELEGRAM_APPLICATION_TOKEN`: Telegram bot token
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`: Neo4j database credentials
- PostgreSQL credentials (handled by docker-compose)


# Code Guidelines

- Never use Any type in mypy.
- All environment variables are read in `backend/src/dependencies.py`. Do not read environment variables directly in other modules - pass them as parameters instead.
- Always use lazy % formatting in logging functions, for example `logger.info("This is a log line for %s", "abc")`
- Do not add docstrings on functions, classes or modules

