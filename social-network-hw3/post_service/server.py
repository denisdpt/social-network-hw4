import sys
sys.path.append("/app")
from concurrent import futures
import grpc
import datetime
import threading

from grpc_stubs import post_pb2, post_pb2_grpc

_posts = {}
_next_id = 1
_lock = threading.Lock()

def generate_post_id():
    global _next_id
    with _lock:
        pid = _next_id
        _next_id += 1
    return pid

def post_to_message(post):
    return post_pb2.Post(
        id=post['id'],
        title=post['title'],
        description=post['description'],
        creator_id=post['creator_id'],
        created_at=post['created_at'],
        updated_at=post['updated_at'],
        is_private=post['is_private'],
        tags=post['tags']
    )

class PostServiceServicer(post_pb2_grpc.PostServiceServicer):
    def CreatePost(self, request, context):
        pid = generate_post_id()
        now = datetime.datetime.utcnow().isoformat()
        post = {
            "id": pid,
            "title": request.title,
            "description": request.description,
            "creator_id": request.creator_id,
            "created_at": now,
            "updated_at": now,
            "is_private": request.is_private,
            "tags": list(request.tags),
        }
        _posts[pid] = post
        return post_pb2.PostResponse(post=post_to_message(post))
    
    def UpdatePost(self, request, context):
        pid = request.id
        if pid not in _posts:
            context.abort(grpc.StatusCode.NOT_FOUND, "Post not found")
        post = _posts[pid]
        post['title'] = request.title
        post['description'] = request.description
        post['is_private'] = request.is_private
        post['tags'] = list(request.tags)
        post['updated_at'] = datetime.datetime.utcnow().isoformat()
        _posts[pid] = post
        return post_pb2.PostResponse(post=post_to_message(post))
    
    def DeletePost(self, request, context):
        pid = request.id
        if pid not in _posts:
            context.abort(grpc.StatusCode.NOT_FOUND, "Post not found")
        post = _posts[pid]
        if post['creator_id'] != request.creator_id:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "No permission to delete this post")
        del _posts[pid]
        return post_pb2.DeletePostResponse(success=True)
    
    def GetPost(self, request, context):
        pid = request.id
        if pid not in _posts:
            context.abort(grpc.StatusCode.NOT_FOUND, "Post not found")
        post = _posts[pid]
        if post['is_private'] and request.requester_id != post['creator_id']:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Access denied")
        return post_pb2.PostResponse(post=post_to_message(post))
    
    def ListPosts(self, request, context):
        creator_id = request.creator_id
        posts_list = [post for post in _posts.values() if post["creator_id"] == creator_id]
        total = len(posts_list)
        page = request.page if request.page > 0 else 1
        page_size = request.page_size if request.page_size > 0 else 10
        start = (page - 1) * page_size
        end = start + page_size
        paginated = posts_list[start:end]
        posts_messages = [post_to_message(p) for p in paginated]
        return post_pb2.ListPostsResponse(posts=posts_messages, total=total)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    post_pb2_grpc.add_PostServiceServicer_to_server(PostServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC Post Service running on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
