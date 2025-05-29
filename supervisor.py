from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import asyncio
import json

async def main():
    consumer = AIOKafkaConsumer(
        'qachat',
        bootstrap_servers='localhost:9092',
        group_id='agent2',
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=False,
    )
    await consumer.start()

    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        linger_ms=0,
    )
    await producer.start()

    try:
        async for message in consumer:
            question = message.value.get("q")
            session_id = message.value.get("session_id")
            print("LLM Received:", question)
    
            from test_agent import stream_agent_response_async
            async for token in stream_agent_response_async(question):
                await producer.send_and_wait('qachat_response',{"ans": "".join(token), "session_id": session_id,})
                await producer.flush()
            await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())