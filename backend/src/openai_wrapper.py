from fastapi import APIRouter, Depends
from openai import OpenAI
from openai.resources.models import Model, SyncPage

from dependencies import get_openai_client

openai_router = APIRouter()


@openai_router.get("/models", response_model=SyncPage[Model])
async def list_models(openai: OpenAI = Depends(get_openai_client)):
    return openai.models.list()
