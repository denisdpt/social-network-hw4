import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch
from httpx import AsyncClient
from httpx import ASGITransport
from main import app

transport = ASGITransport(app=app)

@pytest.mark.asyncio
@patch("main.view_post", return_value=True)
async def test_view_post(mock_view):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/view", json={"client_id": "test_user", "post_id": "1"})
    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_view.assert_called_once()

@pytest.mark.asyncio
@patch("main.like_post", return_value=True)
async def test_like_post(mock_like):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/like", json={"client_id": "test_user", "post_id": "1"})
    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_like.assert_called_once()

@pytest.mark.asyncio
@patch("main.comment_post", return_value="mocked_comment_id")
async def test_comment_post(mock_comment):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/comment", json={
            "client_id": "test_user",
            "post_id": "1",
            "text": "Комментарий"
        })
    assert response.status_code == 200
    assert response.json()["comment_id"] == "mocked_comment_id"
    mock_comment.assert_called_once()

@pytest.mark.asyncio
@patch("main.get_comments", return_value={
    "comments": [
        {"comment_id": "1", "client_id": "test_user", "text": "Комментарий", "timestamp": "2025-04-25T12:00:00"}
    ],
    "total_pages": 1
})
async def test_get_comments(mock_get_comments):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/comments/1", params={"page": 1, "page_size": 10})
    assert response.status_code == 200
    assert isinstance(response.json()["comments"], list)
    mock_get_comments.assert_called_once()
