import grpc
from gen.python import qachat_pb2
from gen.python import qachat_pb2_grpc

import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from datetime import datetime

import json



class LLMAgentServicer(qachat_pb2_grpc.LLMAgentServicer):
    def __init__(self):
        # self.bootstrap_servers = 'localhost:9092'
        self.bootstrap_servers = 'kafka:29092'
        self.topic_request = 'qachat'
        self.topic_response = 'qachat_response'
        self.session_id = 1 # Fix cứng
    
    async def GetListAnswers(self, request, context):
        question = request.q
        print(f"[RECEIVE FROM CLIENT] {datetime.now()}: {question}")
        
        producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await producer.start()
        try:
            await producer.send_and_wait(self.topic_request, {
                "q": question,
                "session_id": self.session_id,
                })
        finally:
            await producer.stop()

        consumer = AIOKafkaConsumer(
            'qachat_response',
            bootstrap_servers=self.bootstrap_servers,
            group_id="server1",
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=False,
        )
        
        await consumer.start()
        try:
            async for msg in consumer:
                await consumer.commit()
                token = msg.value.get("ans")
                session_id = msg.value.get("session_id")
                if session_id != self.session_id:
                    continue
                print(token, end="", flush=True)
                if token == "[DONE]":
                    print()
                    break
                yield qachat_pb2.AnswerResponse(ans=token)
        finally:
            await consumer.stop()
            
            

    async def GetAnswer(self, request, context):
        question = request.q
        print(f"[RECEIVE FROM CLIENT] {datetime.now()}: {question}")
        
        producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await producer.start()
        try:
            await producer.send_and_wait(self.topic_request, {
                "q": question,
                "session_id": self.session_id,
                })
        finally:
            await producer.stop()

        consumer = AIOKafkaConsumer(
            'qachat_response',
            bootstrap_servers=self.bootstrap_servers,
            group_id="server1",
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=False,
        )
        
        await consumer.start()
        try:
            async for msg in consumer:
                await consumer.commit()
                response_session_id = msg.value.get("session_id")
                if response_session_id != self.session_id:
                    continue

                full_answer = msg.value.get("ans", "")
                print(f"{full_answer}")
                return qachat_pb2.AnswerResponse(ans=full_answer)
        finally:
            await consumer.stop()
            
        # return qachat_pb2.AnswerResponse(ans="Hello, I'm an assistant. Nice to meet you!")
        
        
        
        

async def serve():
    server = grpc.aio.server()
    qachat_pb2_grpc.add_LLMAgentServicer_to_server(
        LLMAgentServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    print("Server started at port 50051")
    await server.start()
    await server.wait_for_termination()    

if __name__ == "__main__":
    asyncio.run(serve())