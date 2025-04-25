from fastapi import FastAPI
from grpc_client import view_post, like_post, comment_post, get_comments
from pydantic import BaseModel
from typing import List

app = FastAPI()

class ViewRequest(BaseModel):
    client_id: str
    post_id: str

@app.post("/view")
def view(data: ViewRequest):
    return {"success": view_post(data.client_id, data.post_id)}

class LikeRequest(BaseModel):
    client_id: str
    post_id: str

@app.post("/like")
def like(data: LikeRequest):
    return {"success": like_post(data.client_id, data.post_id)}

class CommentRequest(BaseModel):
    client_id: str
    post_id: str
    text: str

@app.post("/comment")
def comment(data: CommentRequest):
    return {"comment_id": comment_post(data.client_id, data.post_id, data.text)}

@app.get("/comments/{post_id}")
def comments(post_id: str, page: int = 1, page_size: int = 10):
    return get_comments(post_id, page, page_size)
