from fastapi.testclient import TestClient

from app.entity.suggestion import Platform, SuggestionResp, SuggestionType
from app.routers.suggestion import FIRST_SAMPLE
from app.server import app

client = TestClient(app)


def test_get_suggestion_requires_token():
    # ACT
    response = client.get("/v1/suggestions")

    # ASSERT
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid credentials data",
    }


def test_get_suggestions_invalid_platform_param():
    # ARRANGE
    headers = {"Authorization": "Bearer test"}

    # ACT
    response = client.get("/v1/suggestions?platform=IOS", headers=headers)

    # ASSERT
    assert response.status_code == 422


def test_get_suggestions_for_web():
    # ARRANGE
    headers = {"Authorization": "Bearer test"}

    # ACT
    response = client.get("/v1/suggestions?platform=WEB", headers=headers)

    # ASSERT
    assert response.status_code == 200
    resp = SuggestionResp.model_validate(response.json())
    assert resp.type == SuggestionType.WELCOME
    assert resp.platform == Platform.WEB
    assert len(resp.suggestions) == 4
    assert resp.suggestions[0].content == FIRST_SAMPLE
    assert len(resp.thread_id) > 0


def test_get_suggestions_for_mobile():
    # ARRANGE
    headers = {"Authorization": "Bearer test"}

    # ACT
    response = client.get("/v1/suggestions?platform=MOBILE", headers=headers)

    # ASSERT
    assert response.status_code == 200
    resp = SuggestionResp.model_validate(response.json())
    assert resp.type == SuggestionType.WELCOME
    assert resp.platform == Platform.MOBILE
    assert len(resp.suggestions) == 4
    assert resp.suggestions[0].content == FIRST_SAMPLE
    assert len(resp.thread_id) > 0


def test_get_suggestions_missing_platform_param():
    # ARRANGE
    headers = {"Authorization": "Bearer test"}

    # ACT
    response = client.get("/v1/suggestions", headers=headers)

    # ASSERT
    assert response.status_code == 200
    resp = SuggestionResp.model_validate(response.json())
    assert resp.type == SuggestionType.WELCOME
    assert resp.platform == Platform.WEB
    assert len(resp.suggestions) == 4
    assert resp.suggestions[0].content == FIRST_SAMPLE
    assert len(resp.thread_id) > 0
