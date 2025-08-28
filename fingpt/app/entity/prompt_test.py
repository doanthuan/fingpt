from langchain_core.prompts import ChatPromptTemplate
from langfuse.model import ChatMessageDict

from app.core.config import settings
from app.entity.prompt import ChatPrompt


def test_llm_model_default_config(mocker):
    mock_ai_wrapper = mocker.patch("app.entity.prompt.AzureChatOpenAIWrapper")
    mocker.patch.object(settings, "azure_openai_deployment", "test_deployment")
    mocker.patch.object(settings, "llm_temperature", 0.7)
    mocker.patch.object(settings, "openai_api_version", "v1")
    name = "test_prompt"
    chat_messages = [ChatMessageDict(role="user", content="Hello")]
    tmpl = ChatPromptTemplate.from_messages([("system", "fake instruction")])
    chat_prompt = ChatPrompt(
        name=name,
        chat_messages=chat_messages,
        tmpl=tmpl,
    )
    mock_instance = mock_ai_wrapper.return_value
    llm_model = chat_prompt.llm_model

    mock_ai_wrapper.assert_called_once_with(
        azure_deployment="test_deployment", temperature=0.7, api_version="v1"
    )
    assert llm_model == mock_instance


def test_llm_model_remote_config(mocker):
    chat_messages = [ChatMessageDict(role="user", content="Hello")]
    tmpl = ChatPromptTemplate.from_messages([("system", "fake instruction")])
    mock_ai_wrapper = mocker.patch("app.entity.prompt.AzureChatOpenAIWrapper")
    mocker.patch.object(settings, "azure_openai_deployment", "test_deployment")
    mocker.patch.object(settings, "llm_temperature", 0.7)
    mocker.patch.object(settings, "openai_api_version", "v1")

    chat_prompt = ChatPrompt(
        name="test_2",
        chat_messages=chat_messages,
        tmpl=tmpl,
        config={
            "azure_deployment": "remote_deployment",
            "temperature": 0.5,
            "api_version": "v2",
        },
    )
    llm_model = chat_prompt.llm_model

    mock_ai_wrapper.assert_called_once_with(
        azure_deployment="remote_deployment", temperature=0.5, api_version="v2"
    )
    assert llm_model == mock_ai_wrapper.return_value
