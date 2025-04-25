import os
import grpc
from typing import List

from fastapi import FastAPI, HTTPException, Query, Depends, Header, status
from pydantic import BaseModel, Field, validator
from google.protobuf.json_format import MessageToDict
from jose import jwt, JWTError

from grpc_stubs import post_pb2, post_pb2_grpc

app = FastAPI(
    title="Posts API Gateway",
    description="REST API для управления постами через gRPC"
)

GRPC_POST_SERVICE_HOST = os.getenv("GRPC_POST_SERVICE_HOST", "post-service")
GRPC_POST_SERVICE_PORT = os.getenv("GRPC_POST_SERVICE_PORT", "50051")

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"


def get_grpc_stub():
    channel = grpc.insecure_channel(f"{GRPC_POST_SERVICE_HOST}:{GRPC_POST_SERVICE_PORT}")
    return post_pb2_grpc.PostServiceStub(channel)


def get_current_user_id(authorization: str = Header(...)) -> int:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not str(user_id).isdigit():
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return int(user_id)
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=1000)
    is_private: bool = False
    tags: List[str] = Field(default_factory=list, max_items=10)

    @validator("tags", each_item=True)
    def validate_tag_length(cls, v):
        if len(v) > 30:
            raise ValueError("Each tag must be 30 characters or fewer")
        return v


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    pass


def handle_grpc_errors(call):
    try:
        return call()
    except grpc.RpcError as e:
        code = e.code()
        if code == grpc.StatusCode.PERMISSION_DENIED:
            raise HTTPException(status_code=403, detail="Access denied")
        elif code == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Post not found")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/posts")
def create_post(post: PostCreate, user_id: int = Depends(get_current_user_id)):
    stub = get_grpc_stub()
    request = post_pb2.CreatePostRequest(
        title=post.title,
        description=post.description,
        creator_id=user_id,
        is_private=post.is_private,
        tags=post.tags
    )
    response = handle_grpc_errors(lambda: stub.CreatePost(request))
    return MessageToDict(response.post, preserving_proto_field_name=True)


@app.put("/posts/{post_id}")
def update_post(post_id: int, post: PostUpdate, user_id: int = Depends(get_current_user_id)):
    stub = get_grpc_stub()
    get_response = handle_grpc_errors(
        lambda: stub.GetPost(post_pb2.GetPostRequest(id=post_id, requester_id=user_id))
    )
    if get_response.post.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot update another user's post")

    request = post_pb2.UpdatePostRequest(
        id=post_id,
        title=post.title,
        description=post.description,
        is_private=post.is_private,
        tags=post.tags
    )
    response = handle_grpc_errors(lambda: stub.UpdatePost(request))
    return MessageToDict(response.post, preserving_proto_field_name=True)


@app.delete("/posts/{post_id}")
def delete_post(post_id: int, user_id: int = Depends(get_current_user_id)):
    stub = get_grpc_stub()
    request = post_pb2.DeletePostRequest(id=post_id, creator_id=user_id)
    handle_grpc_errors(lambda: stub.DeletePost(request))
    return {"detail": "Post deleted"}


@app.get("/posts/{post_id}")
def get_post(post_id: int, user_id: int = Depends(get_current_user_id)):
    stub = get_grpc_stub()
    request = post_pb2.GetPostRequest(id=post_id, requester_id=user_id)
    response = handle_grpc_errors(lambda: stub.GetPost(request))
    return MessageToDict(response.post, preserving_proto_field_name=True)


@app.get("/posts")
def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    user_id: int = Depends(get_current_user_id)
):
    stub = get_grpc_stub()
    request = post_pb2.ListPostsRequest(
        creator_id=user_id,
        page=page,
        page_size=page_size
    )
    response = handle_grpc_errors(lambda: stub.ListPosts(request))
    posts = [MessageToDict(p, preserving_proto_field_name=True) for p in response.posts]
    return {"posts": posts, "total": response.total}