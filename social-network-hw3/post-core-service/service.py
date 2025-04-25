from post_pb2 import ViewPostResponse, LikePostResponse, CommentPostResponse, GetCommentsResponse, Comment
from post_pb2_grpc import PostServiceServicer
from kafka_producer import send_event
from datetime import datetime

class PostService(PostServiceServicer):
    def ViewPost(self, request, context):
        send_event("post_views", {
            "client_id": request.client_id,
            "post_id": request.post_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        return ViewPostResponse(success=True)

    def LikePost(self, request, context):
        send_event("post_likes", {
            "client_id": request.client_id,
            "post_id": request.post_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        return LikePostResponse(success=True)

    def CommentPost(self, request, context):
        send_event("post_comments", {
            "client_id": request.client_id,
            "post_id": request.post_id,
            "text": request.text,
            "timestamp": datetime.utcnow().isoformat()
        })
        return CommentPostResponse(comment_id="generated_comment_id")

    def GetComments(self, request, context):
        comments = [
            Comment(comment_id="1", client_id="123", text="Nice post!", timestamp=datetime.utcnow().isoformat())
        ]
        return GetCommentsResponse(comments=comments, total_pages=1)
