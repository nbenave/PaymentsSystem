import json
from asgiref.wsgi import WsgiToAsgi

import asyncio
import os
import time
from uuid import uuid4
import logging
import sys
from flask import Flask, request, jsonify, make_response
from jsonschema import validate, ValidationError
from load_config import load_config, load_schema
from rabbitmq_handler import publish_request
from Payment import ResponseCode, PaymentRequest

# load mounted schema into local env
load_config('flask_cm')

# load json schema for payment validadtion
schema = load_schema()

#logger = logging.getLogger(__name__)
#logger.setLevel(os.environ['LOG_LEVEL'])
#logging.basicConfig(format=os.environ['LOG_FORMAT'], stream=sys.stdout)

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)


@app.errorhandler(ResponseCode.NOT_FOUND.value)
def handle_not_found_error(error):
    """
    response error for unhandled endpoint
    :param error:
    :return:
    """
    pr = PaymentRequest(request=request.path,
                   request_method=request.method,
                   response_message={'response':'Page not found'},
                   response_code=ResponseCode.NOT_FOUND.value)
    #logger.error(f'Err endpoint {request.path}')
    return jsonify(pr.as_dict()), pr.response_code


def validate_request_schema(data: dict) -> bool:
    """
    validate json schema
    validate json schema
    :param data:
    :return: True/False
    """
    try:
        validate(data, schema)
    except ValidationError as e:
        logging.warning(f'Err in validation message : {e.message}')
        return False
    else:
        return True



@app.route('/', methods=['GET'])
def hello():
    """
    used for sanity check
    :return:
    """
    response = {'message': f'Hello [{uuid4()}]'}
    return response

def process_payment(path,limit,method):
    """

    :param path: request path
    :param limit: num of records to query from db
    :param method: request method
    :return: payment request object contains data
    """
    start = time.time()
    if not limit:
        limit = os.environ["LIMIT_GET_DEFAULT"]
    path = "/".join([path,str(limit)])
    pr = PaymentRequest(request=path,
                        request_method=method)
    app.logger.info(f'publish request {pr}')
    response = publish_request(request_data=pr.as_dict())
    pr.response_message = json.loads(response)
    pr.response_code = ResponseCode.OK.value
    app.logger.info(f'Get Response: {pr}')
    pr.duration = time.time() - start
    return pr


@app.route('/payment_methods', methods=['GET'])
def get_payment_methods():
    """
    process requests to get payment_methods_id from db
    :return:
    """
    pr = process_payment(request.path,request.args.get('limit'),request.method.lower())
    return jsonify(pr.as_dict()), pr.response_code


@app.route('/payees', methods=['GET'])
def payees():
    """
    process requests to get payee_id from db
    :return:
    """
    pr = process_payment(request.path, request.args.get('limit'),request.method)
    return jsonify(pr.as_dict()), pr.response_code


@app.route('/payment', methods=['POST'])
async def payment():
    """
    input - json data
    - validate message schema before processing
    - Create request Object
    - publish_request and wait for response in dynamic exclusive queue
    measure
    :return: response, response-code
    """
    app.logger.info(f'process payment request')
    start = time.time()
    request_message = request.get_json()
    if validate_request_schema(request_message):
        pr = PaymentRequest(request=request_message,
                            request_method=request.method.lower())

        response = await publish_request(request_data=pr.as_dict())
        pr.response_message = json.loads(response)
        pr.response_code = ResponseCode.OK.value
        pr.duration = time.time() - start
        return jsonify(pr.as_dict()), pr.response_code
    app.logger.warning(f'schema validation failed')
    return jsonify(request_message), ResponseCode.BAD_REQUEST.value


if __name__ == '__main__':
    """
    run flask app in debug mode
    """
    asgi_app.run(host='0.0.0.0', port=int(os.environ['APP_PORT']))
