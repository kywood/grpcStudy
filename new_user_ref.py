class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = set()  # 중복을 방지하기 위해 set 사용
        self.lock = threading.Lock()

    def NotifyUserCount(self, request_iterator, context):
        is_new_connection = False
        with self.lock:
            # 이전에 같은 context가 추가되지 않았는지 확인
            if context not in self.clients:
                self.clients.add(context)
                is_new_connection = True

        if is_new_connection:
            # 새로운 접속인 경우에만 접속자 수 업데이트 및 알림
            message = f"hello 현재 {len(self.clients)} 명 접속중입니다."
            context.write(chat_pb2.UserStreamResponse(responseMessage=message))

        try:
            for request in request_iterator:
                if request.message == "getCurrentUsersCount":
                    # 모든 클라이언트에게 현재 접속자 수 브로드캐스트
                    current_count = len(self.clients)
                    self.broadcast_message(chat_pb2.UserStreamResponse(currentCount=current_count))
                elif request.message == "ping":
                    # 요청한 클라이언트에게만 "pong"으로 응답
                    context.write(chat_pb2.UserStreamResponse(responseMessage="pong"))
        finally:
            with self.lock:
                if context in self.clients:
                    self.clients.remove(context)