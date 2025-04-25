from confluent_kafka import Producer
import json
import time

producer = None

def get_producer():
    global producer
    if producer is not None:
        return producer

    for i in range(10):
        try:
            print(f"[Kafka] Попытка подключения {i+1}/10...")
            p = Producer({'bootstrap.servers': 'kafka:9092'})
            p.list_topics(timeout=5)
            print("[Kafka] Подключение к Kafka установлено")
            producer = p
            return producer
        except Exception as e:
            print(f"[Kafka] Ошибка подключения: {e}")
            time.sleep(3)

    raise RuntimeError("Не удалось подключиться к Kafka после нескольких попыток")

def send_event(topic: str, data: dict):
    p = get_producer()
    p.produce(topic, json.dumps(data).encode('utf-8'))
    p.flush()