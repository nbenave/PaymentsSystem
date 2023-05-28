import json
import pika
import logging
import sys
import os
from typing import Dict,Callable
from load_config import load_config
from RiskAnalysis import RiskAnalysis, RiskMessage, DataclassEncoder
load_config('risk_engine_cm')

logger = logging.getLogger(__name__)
logger.setLevel(os.environ['LOG_LEVEL'])
logging.basicConfig(format=os.environ['LOG_FORMAT'], stream=sys.stdout)

class RiskEngine:
    def __init__(self):
        self._risk_analysis = RiskAnalysis()
        self._username = str(os.environ['RABBITMQ_USERNAME'])
        self._password = str(os.environ['RABBITMQ_PASSWORD'])
        self._rabbitmq_host = os.environ['RMQ_HOST']
        self._rabbitmq_port = int(os.environ['RMQ_PORT'])
        self._consume_queue = os.environ['RMQ_CONSUME_REQUESTS_QUEUE']
        self._consume_queue_rk = os.environ['RMQ_CONSUME_REQUESTS_QUEUE_RK']
        self._requests_post_queue = os.environ['RMQ_METHOD_POST_QUEUE']
        self._requests_post_rk = os.environ['RMQ_METHOD_POST_RK']
        self._requests_get_queue = os.environ['RMQ_METHOD_GET_QUEUE']
        self._requests_get_rk = os.environ['RMQ_METHOD_GET_RK']
        self._exchange = os.environ['RMQ_EXCHANGE']
        self._exchange_type = os.environ['RMQ_EXCHANGE_TYPE']
        self._response_exchange = os.environ['RMQ_RESPONSE_EXCHANGE']
        self._unhandled_method_rk = os.environ['RMQ_UNHANDLED_RK']
        self._unhandled_methods_queue = os.environ['RMQ_UNHANDLED_METHODS_QUEUE']
        self._prefetch_count = int(os.environ['RMQ_PREFETCH_COUNT'])

        self._creds = None
        self._params = None
        self._connection = None
        self._channel = None

    def rmq_connect(self) -> None:
        """
        connect to rabbitmq broker
        """
        self._creds = pika.PlainCredentials(username=self._username, password=self._password)
        self._params = pika.ConnectionParameters(host=self._rabbitmq_host, port=self._rabbitmq_port, credentials=self._creds)
        self._connection = pika.BlockingConnection(parameters=self._params)
        self._channel = self._connection.channel()
        logger.info(f'Connected to RMQ : {self._channel}')

    def process_message(self, request: Dict, risk_object: RiskMessage) -> (Dict, str):
        """
        :param request: the request from the client
        :param risk_object: risk analysis parameters performed on request
        :return: request, routing key
        """
        request['risk_state'] = risk_object.risk_state
        request['risk_level'] = risk_object.risk_level
        rest_rk = request.get('request_method', self._unhandled_method_rk).lower()
        return request, rest_rk
    def forward_request_to_dal(self, request: Dict, risk_object: RiskMessage, reply_to: str , correlation_id: str) -> None:
        """
        process the request after risk analysis to dal application
        rest_rk is determined by the request method
        set reply-to and correlation in properties to route response to dynamic queue
        :return:
        """
        request, rest_rk = self.process_message(request, risk_object)
        logger.info(f'forward request to dal')
        self._channel.basic_publish(exchange=self._exchange,
                                    routing_key=rest_rk,
                                    properties=pika.BasicProperties(
                                        reply_to=reply_to,
                                        correlation_id=correlation_id
                                    ),
                                    body=json.dumps(request,cls=DataclassEncoder))

    def on_message(self, channel, method, properties, body):
        """
        perform risk analysis for a request
        forward the message to dal
        """
        payment_message = json.loads(body.decode())
        logger.info(f'Received message from my_queue : {payment_message}')
        risk_obj = self._risk_analysis.do_risk_analysis(payment_message)
        self.forward_request_to_dal(request=payment_message,
                                    risk_object=risk_obj,
                                    reply_to=properties.reply_to,
                                    correlation_id=properties.correlation_id)

        self._channel.basic_ack(delivery_tag=method.delivery_tag)
    def setup_mq(self) -> None:
        """
        declare and bind queues
        setup qos
        """
        self._channel.queue_declare(queue=self._consume_queue, durable=True)
        self._channel.queue_declare(queue=self._unhandled_methods_queue, durable=True)
        self._channel.queue_declare(queue=self._requests_post_queue, durable=True)
        self._channel.queue_declare(queue=self._requests_get_queue, durable=True)

        self._channel.exchange_declare(exchange=self._exchange,
                                       exchange_type=self._exchange_type,
                                       durable=True)
        # Bind income requests
        self._channel.queue_bind(queue=self._consume_queue,
                                 exchange=self._exchange,
                                 routing_key=self._consume_queue_rk)

        # Bind POST requests
        self._channel.queue_bind(queue=self._requests_post_queue,
                                 exchange=self._exchange,
                                 routing_key=self._requests_post_rk)
        # Bind GET requests
        self._channel.queue_bind(queue=self._requests_get_queue,
                                 exchange=self._exchange,
                                 routing_key=self._requests_get_rk)
        # Bind unhandled rest methods
        self._channel.queue_bind(queue=self._unhandled_methods_queue,
                                 exchange=self._exchange,
                                 routing_key=self._unhandled_method_rk)

        self._channel.basic_qos(prefetch_count=self._prefetch_count)

    def run(self) -> None:
        """
        execute thread for handles batches
        start consuming from queue
        """
        self.rmq_connect()
        self.setup_mq()

        self._channel.basic_consume(queue=self._consume_queue, on_message_callback=self.on_message)
        logger.info(f'[*] Risk engine app started. Waiting for message in Queue {self._consume_queue} [*]')
        self._channel.start_consuming()



