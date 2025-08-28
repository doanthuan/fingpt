import json
from unittest.mock import AsyncMock, patch

import pytest

from app.assistant_v2.transfer.graph.tool.get_contacts import _get_contacts
from app.entity import Contact


@pytest.mark.asyncio
async def test_get_contacts_success(agent_config):
    # Mock the list_contacts function
    contacts = [
        Contact(id="1", name="Alex"),
        Contact(id="2", name="Bob"),
        Contact(id="3", name="Alexandra"),
    ]
    mock_contacts = AsyncMock(return_value=contacts)
    with patch(
        "app.assistant_v2.transfer.graph.tool.get_contacts.list_contacts", mock_contacts
    ):
        # Create a mock config

        # Call the function
        result = await _get_contacts("alex", agent_config, {})

        # Assertions
        result_list = eval(result)
        result_contacts = [Contact(**json.loads(contact)) for contact in result_list]
        assert result_contacts == [contacts[0], contacts[2]]


@pytest.mark.asyncio
async def test_get_contacts_failure(agent_config):
    # Mock the list_contacts function to raise an exception
    with patch(
        "app.assistant_v2.transfer.graph.tool.get_contacts.list_contacts",
        side_effect=Exception("API error"),
    ):
        # Call the function and expect an exception
        with pytest.raises(Exception, match="API error"):
            await _get_contacts("some_name", agent_config, {})
