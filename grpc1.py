from concurrent import futures
import grpc
import chat_pb2
import chat_pb2_grpc
import threading

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = []
        self.lock = threading.Lock()

    def streamChannel(self, request_iterator, context):
        with self.lock:
            self.clients.append(context)

        try:
            for request in request_iterator:
                if request.message == "login":
                    # login 요청에 대한 응답: 해당 클라이언트에게만 환영 메시지 전송
                    message = f"hello 현재 {len(self.clients)} 명 접속중입니다."
                    context.write(chat_pb2.StreamResponse(responseMessage=message))
                elif request.message == "getCurrentUsersCount":
                    # getCurrentUsersCount 요청에 대한 응답: 모든 클라이언트에게 접속자 수 브로드캐스트
                    current_count = len(self.clients)
                    self.broadcast_message(chat_pb2.StreamResponse(currentCount=current_count))
                elif request.message == "ping":
                    # ping 요청에 대한 응답: 해당 클라이언트에게만 "pong"으로 응답
                    context.write(chat_pb2.StreamResponse(responseMessage="pong"))

        finally:
            with self.lock:
                self.clients.remove(context)

    def broadcast_message(self, message):
        """모든 클라이언트에게 메시지 브로드캐스트"""
        with self.lock:
            for client in self.clients:
                try:
                    client.write(message)
                except Exception as e:
                    print(f"Error broadcasting message to client: {e}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()