from dependency_injector import containers, providers
from langchain_chroma import Chroma
from langchain_openai.embeddings import AzureOpenAIEmbeddings

from app.assistant_v2.assistant_module import AssistantModule
from app.auth.auth_module import AuthModule
from app.command.command_module import CommandModule
from app.core.config import settings
from app.intent.intent_module import IntentModule
from app.profile.profile_module import ProfileModule
from app.ticker.ticker_module import TickerModule
from app.utils import SemanticCache


class ServerContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            __name__,
            "app.routers.raw_data_report",
            "app.routers.backbase_auth",
            "app.routers.assistant_chat",
            "app.routers.command",
            "app.routers.profile",
            "app.routers.intent",
        ]
    )

    ticker_module = providers.Container(TickerModule)
    auth_module = providers.Container(AuthModule)
    assistant_module = providers.Container(AssistantModule)
    command_module = providers.Container(CommandModule)
    profile_module = providers.Container(ProfileModule)
    intent_module = providers.Container(IntentModule)

    emb_srv: providers.Provider[AzureOpenAIEmbeddings] = providers.Singleton(
        AzureOpenAIEmbeddings, azure_deployment=settings.azure_text_embedding_deployment
    )
    chroma: providers.Provider[Chroma] = providers.Singleton(
        Chroma,
        collection_name=settings.chroma_collection_name,
        embedding_function=emb_srv,
        persist_directory=settings.chroma_persist_dir,
        collection_metadata={"hnsw:space": settings.chroma_search_distance},
        create_collection_if_not_exists=True,
    )
    semantic_cache: providers.Provider[SemanticCache] = providers.Singleton(
        SemanticCache,
        vector_store_srv=chroma,
        emb_srv=emb_srv,
        score_threshold=0.9,
    )
