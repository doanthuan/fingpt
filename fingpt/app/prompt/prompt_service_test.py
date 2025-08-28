from unittest.mock import MagicMock

from langchain_core.prompts import ChatPromptTemplate

from app.entity import ChatPrompt
from app.prompt.prompt_service import PromptService


async def test_get_prompt(mocker):
    mock_langfuse = MagicMock()
    mock_prompt = MagicMock()
    mock_prompt.config = {}
    content = (
        "content {{variable}} "
        "json: {"
        '"key1": "value1", '
        '"key2": [{"sub_key": "sub_value"}]'
        "}"
    )
    template = (
        "content {variable} "
        "json: {{"
        '"key1": "value1", '
        '"key2": [{{"sub_key": "sub_value"}}]'
        "}}"
    )
    mock_prompt.compile.return_value = [
        {
            "role": "system",
            "content": content,
        },
    ]
    mock_langfuse.get_prompt.return_value = mock_prompt

    mocker.patch(
        "app.prompt.prompt_service.LangfuseSingleton.get", return_value=mock_langfuse
    )
    prompt_service = PromptService()
    prompt = await prompt_service.get_prompt(
        MagicMock(logger=MagicMock()), "name", "label", "chat"
    )

    expected_prompt = ChatPrompt(
        name="name",
        chat_messages=[{"role": "system", "content": content}],
        tmpl=ChatPromptTemplate.from_messages([("system", template)]),
        config={},
    )
    assert prompt.name == expected_prompt.name
    assert prompt.chat_messages == expected_prompt.chat_messages
    assert prompt.tmpl == expected_prompt.tmpl
    assert prompt.configs == expected_prompt.configs
