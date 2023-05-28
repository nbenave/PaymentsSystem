import json
import time
import uuid
import pika
import os

def publish_request(request_data):
    exchange = os.environ['RMQ_EXCHANGE']
    exchange_type = os.environ['RMQ_EXCHANGE_TYPE']
    host = os.environ['RMQ_HOST']
    port = os.environ['RMQ_PORT']
    rest_requests_queue = os.environ['RMQ_QUEUE']
    rest_requests_rk = os.environ['RMQ_BIND_RK']
    username = str(os.environ['RABBITMQ_USERNAME'])
    password = str(os.environ['RABBITMQ_PASSWORD'])

    credentials = pika.PlainCredentials(username=username, password=password)
    params = pika.ConnectionParameters(host,credentials=credentials, port=int(port))
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # declare and bind configurations
    channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=True)
    channel.exchange_declare(exchange=exchange, exchange_type=exchange_type,durable=True)
    channel.queue_declare(queue=rest_requests_queue, durable=True)
    channel.queue_bind(queue=rest_requests_queue,exchange=exchange,routing_key=rest_requests_rk)

    # dynamic queue declare
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # dynamic queue bind
    channel.queue_bind(exchange=exchange, queue=queue_name)

    # publish the request with reply_to and correlation_id in message properties
    correlation_id = str(uuid.uuid4())
    channel.basic_publish(
        exchange=exchange,
        routing_key=rest_requests_queue,
        properties=pika.BasicProperties(
            reply_to=queue_name,
            correlation_id=correlation_id
        ),
        body=json.dumps(request_data).encode()
    )
    response = {}

    def on_response(ch, method, properties, body):
        if correlation_id == properties.correlation_id:
            response['response'] = body.decode()
            connection.close()

    channel.basic_consume(queue=queue_name, on_message_callback=on_response, auto_ack=True)
    channel.start_consuming()
    while 'response' not in response: # keep the channel alive
        print('Check') # TODO : Verify HB response when not consuming
        connection.process_data_events()

    return response['response']


