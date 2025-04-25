import grpc
import post_pb2
import post_pb2_grpc

channel = grpc.insecure_channel("post-core-service:50051")
stub = post_pb2_grpc.PostServiceStub(channel)

def view_post(client_id, post_id):
    response = stub.ViewPost(post_pb2.ViewPostRequest(client_id=client_id, post_id=post_id))
    return response.success

def like_post(client_id, post_id):
    response = stub.LikePost(post_pb2.LikePostRequest(client_id=client_id, post_id=post_id))
    return response.success

def comment_post(client_id, post_id, text):
    response = stub.CommentPost(post_pb2.CommentPostRequest(client_id=client_id, post_id=post_id, text=text))
    return response.comment_id

def get_comments(post_id, page, page_size):
    response = stub.GetComments(post_pb2.GetCommentsRequest(post_id=post_id, page=page, page_size=page_size))
    return {
        "comments": [dict(comment_id=c.comment_id, client_id=c.client_id, text=c.text, timestamp=c.timestamp) for c in response.comments],
        "total_pages": response.total_pages
    }
