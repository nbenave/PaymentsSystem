import queue
import threading

import pika
from threading import Thread
from queue import Queue
from typing import List,Dict
import time
import psycopg2
import json
import logging
import sys
import os
from load_config import load_config
load_config('dal_cm')

logger = logging.getLogger(__name__)
logger.setLevel(os.environ['LOG_LEVEL'])
logging.basicConfig(format=os.environ['LOG_FORMAT'], stream=sys.stdout)


class DAL:
    def __init__(self):
        self._rabbitmq_username = str(os.environ['RABBITMQ_USERNAME'])
        self._rabbitmq_password = str(os.environ['RABBITMQ_PASSWORD'])
        self._rabbitmq_host = os.environ['RMQ_HOST']
        self._rabbitmq_port = int(os.environ['RMQ_PORT'])
        # configure for setting up mq
        self._consume_get_requests_queue = os.environ['RMQ_METHOD_GET_QUEUE']
        self._consume_post_requests_queue = os.environ['RMQ_METHOD_POST_QUEUE']
        self._requests_post_rk = os.environ['RMQ_METHOD_POST_RK']
        self._requests_get_queue = os.environ['RMQ_METHOD_GET_QUEUE']
        self._requests_get_rk = os.environ['RMQ_METHOD_GET_RK']
        self._exchange = os.environ['RMQ_EXCHANGE']
        self._response_exchange = os.environ['RMQ_RESPONSE_EXCHANGE']
        self._consume_queue = os.environ['CONSUME_QUEUE']
        self._prefetch_count = int(os.environ['PREFETCH_COUNT'])
        self._payment_response = {'APPROVED':os.environ['POST_APPROVED_RESPONSE'],
                                  'REJECTED': os.environ['POST_REJECTED_RESPONSE']}
        self._creds = None
        self._params = None
        self._connection = None
        self._channel = None
        self._pgsql_connection = None
        self._pgsql_cursor = None
        self._batch_size = int(os.environ['BATCH_SIZE'])
        self._batch_timeout = int(os.environ['BATCH_TIMEOUT'])
        self._table_name = os.environ["POSTGRESQL_PAYMENTS_TABLE"]
        self._queue = Queue()
        self._batch_messages = []

    def connect_pgsql(self):
        """
        create connection to postgresql server
        :return:
        """
        self._pgsql_connection = psycopg2.connect(
            host=os.environ['POSTGRESQL_HOST'],
            database=os.environ['POSTGRESQL_DB'],
            user= os.environ['PGSQL_USERNAME'],
            password=os.environ['PGSQL_PASSWORD']
        )
        self._pgsql_cursor = self._pgsql_connection.cursor()

    def connect_rmq(self) -> None:
        """
        connect to rabbitmq broker
        """
        self._creds = pika.PlainCredentials(username=self._rabbitmq_username, password=self._rabbitmq_password)
        self._params = pika.ConnectionParameters(host=self._rabbitmq_host, port=self._rabbitmq_port, credentials=self._creds)
        self._connection = pika.BlockingConnection(parameters=self._params)
        self._channel = self._connection.channel()

    def publish_message(self, message, reply_to: str = None,correlation_id: str = None):
        """
        publish message to queue
        :param message: request message with response
        :param reply_to: the queue client is listening
        :param correlation_id: unique id of message to verify user session
        :return:
        """
        self._channel.basic_publish(exchange='',
                                    routing_key=reply_to,
                                    properties=pika.BasicProperties(
                                        correlation_id=correlation_id
                                    ),
                                    body=json.dumps(message).encode())

    def get_record(self,data: Dict) -> Dict:
        """
        prepeare dict object from request before insert to database
        """
        return {'amount':data['request']['amount'],
                'currency':data['request']['currency'],
                'user_id' : data['request']['user_id'],
                'payee_id': data['request']['payee_id'],
                'payment_method_id': data['request']['payment_method_id'],
                'risk_assessment':data['risk_level'],
                'risk_state':data['risk_state']
                }

    def _insert_records_to_db(self):
        """
        insert data in batch
        opens a connection every batch
        """
        columns = ', '.join(self._batch_messages[0].keys())
        values_list = []
        for message in self._batch_messages:
            record = [str(v) for v in message.values()]
            values_list.append(record)

        # clear list
        self._batch_messages.clear()
        query = f"INSERT INTO {self._table_name} ({columns}) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        try:
            self.connect_pgsql()
            self._pgsql_cursor.executemany(query, values_list)
            num_of_rows_inserted = self._pgsql_cursor.rowcount
            logger.info(f'Insert {num_of_rows_inserted} num of rows')
            self._pgsql_connection.commit()
        except psycopg2.Error as e:
            logger.error(f'Err while insert batch : ({e})')
            raise Exception(e)
    def _handles_batches(self,_queue):
        """
        :param _queue: get messages from on_message callback
        insert data in batches or timeout using insert_records_to_db()
        """
        while True:
            try:
                data = _queue.get(block=True,timeout=self._batch_timeout)
                record = self.get_record(data)
                self._batch_messages.append(record)
                if len(self._batch_messages) >= self._batch_size:
                    self._insert_records_to_db()
            except queue.Empty:
                if len(self._batch_messages) > 0 :
                    self._insert_records_to_db()

    def execute_select_query(self,request: str) -> List:
        """
        execute get query from database
        connect to db on every request
        return: list of records
        """
        _, column_name, limit = request.split('/')
        column_name = os.environ[column_name.upper()]
        query = f"SELECT {column_name} FROM {self._table_name} LIMIT {limit} ;"
        try:
            self.connect_pgsql()
            self._pgsql_cursor.execute(query)
            records = self._pgsql_cursor.fetchall()
            self._pgsql_connection.commit()
        except psycopg2.Error as e:
            logger.error(f'Err while insert batch : ({e})')
            raise Exception(e)

        records = [record[0] for record in records]
        logger.info(f'select {len(records)} num of rows')
        return records


    def on_message(self,channel, method, properties, body) -> None:
        """
        callback on message , execute when message in Queue
        if post method - reply directly to client
            then pass the data within queue to insert thread.
        if get method - execute query and retrieve payload, then reply to client
        """
        request_data = json.loads(body.decode())
        logger.info(f'Get request : {request_data} Reply-to : {properties.reply_to}, Corr : {properties.correlation_id}')
        channel.basic_ack(delivery_tag=method.delivery_tag)
        if request_data.get('request_method').lower() == 'post':
            self.publish_message(message=self._payment_response.get(request_data.get('risk_state')),
                                 reply_to= properties.reply_to,
                                 correlation_id= properties.correlation_id)
            self._queue.put(request_data)

        elif request_data.get('request_method').lower() == 'get':
            records = self.execute_select_query(request_data['request'])
            self.publish_message(message=records,
                                 reply_to=properties.reply_to,
                                 correlation_id=properties.correlation_id)


    def setup_mq(self) -> None:
        """
        declare and bind queues
        setup qos
        """
        self._channel.queue_declare(queue=self._consume_get_requests_queue, durable=True)
        self._channel.queue_declare(queue=self._consume_post_requests_queue, durable=True)
        self._channel.queue_bind(queue=self._consume_post_requests_queue,
                                 exchange=self._exchange,
                                 routing_key=self._requests_post_rk)
        self._channel.queue_bind(queue=self._consume_get_requests_queue,
                                 exchange=self._exchange,
                                 routing_key=self._requests_get_rk)
        self._channel.basic_qos(prefetch_count=self._prefetch_count)

    def run(self) -> None:
        """
        execute thread for handles batches
        start consuming from queue
        """
        self.connect_rmq()
        self.setup_mq()
        batch_timeout_thread = threading.Thread(target=self._handles_batches,args=(self._queue,))
        batch_timeout_thread.start()

        self._channel.basic_consume(queue=self._consume_queue, on_message_callback=self.on_message)
        # Start consuming messages
        logger.info(f'[*] DAL started. Waiting for message in Queue {self._consume_queue} [*]')
        self._channel.start_consuming()



