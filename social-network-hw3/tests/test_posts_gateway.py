import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import grpc
from google.protobuf.json_format import MessageToDict
from grpc_stubs import post_pb2
from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'api-gateway-posts')))
import main
from main import app

VALID_TOKEN = "Bearer test.jwt.token"

@pytest.fixture(autouse=True)
def mock_jwt():
    app.dependency_overrides[main.get_current_user_id] = lambda: 1
    yield
    app.dependency_overrides = {}


def mock_post_response():
    now = datetime.now(timezone.utc)
    ts = Timestamp()
    ts.FromDatetime(now)

    return MagicMock(
        id=1,
        title="Test",
        description="Desc",
        creator_id=1,
        is_private=False,
        tags=["tag"],
        created_at=ts,
        updated_at=ts
    )


def test_create_post_success():
    client = TestClient(app)
    with patch("main.get_grpc_stub") as mock_stub:
        mock_stub.return_value.CreatePost.return_value.post = mock_post_response()
        response = client.post(
            "/posts",
            headers={"Authorization": VALID_TOKEN},
            json={"title": "Test", "description": "Desc", "is_private": False, "tags": ["tag"]}
        )
        print("RESP:", response.text)
        assert response.status_code == 200
        assert response.json()["title"] == "Test"


def test_create_post_too_long_title():
    client = TestClient(app)
    long_title = "A" * 101
    response = client.post(
        "/posts",
        headers={"Authorization": VALID_TOKEN},
        json={"title": long_title, "description": "desc", "tags": []}
    )
    print("RESP:", response.text)
    assert response.status_code == 422


def test_create_post_unauthorized():
    client = TestClient(app)
    with patch("main.get_grpc_stub"):
        response = client.post(
            "/posts",
            json={"title": "Test", "description": "desc", "tags": []}
        )
        print("RESP:", response.text)
        assert response.status_code in [401, 422]


def test_get_post_success():
    client = TestClient(app)
    with patch("main.get_grpc_stub") as mock_stub:
        mock_stub.return_value.GetPost.return_value.post = mock_post_response()
        response = client.get("/posts/1", headers={"Authorization": VALID_TOKEN})
        print("RESP:", response.text)
        assert response.status_code == 200
        assert response.json()["title"] == "Test"


def test_get_post_not_found():
    client = TestClient(app)
    with patch("main.get_grpc_stub") as mock_stub:
        error = grpc.RpcError()
        error.code = lambda: grpc.StatusCode.NOT_FOUND
        mock_stub.return_value.GetPost.side_effect = error

        response = client.get("/posts/999", headers={"Authorization": VALID_TOKEN})
        print("RESP:", response.text)
        assert response.status_code == 404


def test_update_post_success():
    client = TestClient(app)
    with patch("main.get_grpc_stub") as mock_stub:
        stub = mock_stub.return_value
        stub.GetPost.return_value.post.creator_id = 1
        stub.UpdatePost.return_value.post = mock_post_response()

        response = client.put("/posts/1", headers={"Authorization": VALID_TOKEN},
                              json={"title": "Updated", "description": "New desc", "tags": []})
        print("RESP:", response.text)
        assert response.status_code == 200
        assert response.json()["title"] == "Test"


def test_update_post_not_found():
    client = TestClient(app)
    with patch("main.get_grpc_stub") as mock_stub:
        error = grpc.RpcError()
        error.code = lambda: grpc.StatusCode.NOT_FOUND
        mock_stub.return_value.GetPost.side_effect = error

        response = client.put("/posts/999", headers={"Authorization": VALID_TOKEN},
                              json={"title": "Updated", "description": "New desc", "tags": []})
        print("RESP:", response.text)
        assert response.status_code == 404


def test_delete_post_success():
    client = TestClient(app)
    with patch("main.get_grpc_stub"):
        response = client.delete("/posts/1", headers={"Authorization": VALID_TOKEN})
        print("RESP:", response.text)
        assert response.status_code == 200
        assert response.json()["detail"] == "Post deleted"


def test_delete_post_not_found():
    client = TestClient(app)
    with patch("main.get_grpc_stub") as mock_stub:
        error = grpc.RpcError()
        error.code = lambda: grpc.StatusCode.NOT_FOUND
        mock_stub.return_value.DeletePost.side_effect = error

        response = client.delete("/posts/999", headers={"Authorization": VALID_TOKEN})
        print("RESP:", response.text)
        assert response.status_code == 404