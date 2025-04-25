import grpc
from concurrent import futures
from post_pb2_grpc import add_PostServiceServicer_to_server
from service import PostService

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_PostServiceServicer_to_server(PostService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC сервер запущен на порту 50051.")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
