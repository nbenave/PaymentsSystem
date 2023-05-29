import random
import argparse
import json
from math import ceil
import time
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import requests

# execute
# python demo_post.py --num_of_requests 20 --server nginx
servers = {'nginx': 'a5253817a018c48eb8dc089fc96c18ff-2060703969.eu-central-1.elb.amazonaws.com:80',
        'flask': 'ac3828cb0b1e94a63b8b41fae12c1908-1440347994.eu-central-1.elb.amazonaws.com:8192'}

server = 'nginx'
HOSTNAME = servers[server]

# For debugging
#HOSTNAME = 'localhost'

URL = f'http://{HOSTNAME}/payment'

def send_post_request(url):
    payload = {
        "amount": round(random.random()*10,2),
        "currency": random.choice(["USD","ILS","EUR"]),
        "user_id": str(uuid4()),
        "payee_id": str(uuid4()),
        "payment_method_id": str(uuid4())
    }
    response = requests.post(url,json=payload)

    return response.text

def parallel_requests_generator(url,num_of_requests):
    start = time.time()
    with ThreadPoolExecutor(max_workers=max(200,int(num_of_requests))) as executor:
        responses = executor.map(send_post_request, [url for _ in range(num_of_requests)])
    end = time.time()
    time.sleep(2)
    print(f'Total duration= {round((end - start), 2)}, Total responses= {num_of_requests}, rate= {num_of_requests / (end - start)}')

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_of_requests', type=int, default=5, help='num_of_requests to send')
    parser.add_argument('--server', type=str, default='nginx' , help='rest server , flask or nginx')
    opt = parser.parse_args()
    return vars(opt)

def generate_url(hostname):
    return f'http://{hostname}/payment'

def main(num_of_requests,server):
    hostname= servers[server]
    parallel_requests_generator(generate_url(hostname),num_of_requests)

if __name__ == '__main__':
    opt = parse_opt()
    main(**opt)
