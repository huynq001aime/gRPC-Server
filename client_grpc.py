import grpc
from gen.python import qachat_pb2
from gen.python import qachat_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = qachat_pb2_grpc.LLMAgentStub(channel)

    print("Chatbot gRPC client started. Type '_exit_' to EXIT.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.strip() == "_exit_":
            print("Goodbye!")
            break

        request = qachat_pb2.PromptRequest(q=user_input)
        try:
            print("AimeAgent: ", end="", flush=True)
            # for response in stub.GetListAnswers(request): # Cho server streaming
            #     print(response.ans, end="", flush=True)
            
            response = stub.GetAnswer(request) # Cho server không dùng streaming
            print(response.ans, end="", flush=True)
            print()
        except grpc.RpcError as e:
            print(f"RPC Error: {e.code()} - {e.details()}")
            break

if __name__ == '__main__':
    run()
