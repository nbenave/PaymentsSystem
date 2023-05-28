# Payments System
![Image description](Images/PaymentSystem.png)

## Demo
- Execute `python demo_post.py --num_of_requests XXX --server nginx` to generate requests in parallel  
- Request reply on [`postman`](https://web.postman.co)

## Dashboard, UI and Servers
- [RMQ UI](http://a75b10a42d54343d5807c33c915d4027-772471113.eu-central-1.elb.amazonaws.com:15672)
- [Postgreql Server](http://a787283b2acd446988c17a47e610c552-1989815858.eu-central-1.elb.amazonaws.com:5432)
- [Nginx Server](http://a5253817a018c48eb8dc089fc96c18ff-2060703969.eu-central-1.elb.amazonaws.com:80)
- [Flask Server](http://ac3828cb0b1e94a63b8b41fae12c1908-1440347994.eu-central-1.elb.amazonaws.com:8192)
- [Kubernetes dashboard](https://a3fc3325d3af44a78b2ec3ff0248c1c2-187620913.eu-central-1.elb.amazonaws.com:443)


## API reference 
### Response code
```http
200: Success
201: Created
400: Bad request
404: Not found
```

**Get payment methods:**
```http
GET /payment_methods
```
**Response:**
```http
{
  "duration": 0.32589173316955566,
  "request": "/payment_methods/",
  "request_method": "get",
  "response_code": 200,
  "response_message": [
    "81525cae-559d-4e55-87a4-8bb2c667fcd8",
    "9915c54d-9094-4e0d-bf6d-0b210a088013",
    "25cf859e-46ba-4214-bf93-65f5b26ff7e5",
    "3010db1e-afd3-45b8-889a-10bb1c3b7696",
    ....
  ]
}

```
**Get payees:**
```http
GET /payees
```
**Response:**
```http
{
  "duration": 0.7880330085754395,
  "request": "/payees",
  "request_method": "GET",
  "response_code": 200,
  "response_message": [
    "b0e08b71-30ca-4e32-82df-f8ab98df98de",
    "17522c22-ff05-4bd2-87ff-63d17f4adbf0",
    "bb39f83b-131d-4ba1-99ae-7cd967300226",
    "6624f13b-252b-4211-8f62-ef267dca8a46",
    ...
  ]
}
```
**Create payment:**
```http
POST /payment
```
**Response `APPROVED`:**
```http
 {
  "duration": 0.36794328689575195,
  "request": {
    "amount": 9.77,
    "currency": "ILS",
    "payee_id": "677d7998-c663-4061-8107-51f05f1d43ea",
    "payment_method_id": "c8c9f6f2-65f0-4dd8-9b86-cc7bec038fe7",
    "user_id": "2318c8f1-1eb1-4a36-907a-4bf052b71dfa"
  },
  "request_method": "post",
  "response_code": 200,
  "response_message": "Payment created successfully"
}
```
**Response `REJECTED`:**
```http
{
  "duration": 0.6056997776031494,
  "request": {
    "amount": 9.13,
    "currency": "ILS",
    "payee_id": "3439f702-4b0f-42e1-b583-f6714c57e5b1",
    "payment_method_id": "e68f74d9-dd7d-4546-9c6e-9fbf8eefbb2b",
    "user_id": "9601c3f0-4a44-4b86-bac3-f5db0451924b"
  },
  "request_method": "post",
  "response_code": 200,
  "response_message": "The request has been rejected!"
}

```



## Project tree
```
.
├── connect_to_db.sh
├── DAL
│   ├── app.py
│   ├── DAL.py
│   ├── Dockerfile
│   ├── k8s_files
│   │   ├── dal_cm.yaml
│   │   ├── dal_get_process_deployment.yaml
│   │   ├── dal_hpa.yaml
│   │   ├── dal_post_process_deployment.yaml
│   │   └── dal_secrets.yaml
│   ├── load_config.py
│   └── requirements.txt
├── demo_post.py
├── deploy_scripts
│   ├── dal_build_push.sh
│   ├── dal_deploy.sh
│   ├── flask_build_push.sh
│   ├── flask_deploy.sh
│   ├── risk_build_push.sh
│   ├── risk_deploy.sh
│   └── rmq_helm_deploy.sh
├── flaskApp
│   ├── app.py
│   ├── Dockerfile
│   ├── k8s_files
│   │   ├── flask_cm.yaml
│   │   ├── flask_hpa.yaml
│   │   ├── flask_secrets.yaml
│   │   ├── flask_wsgi_deployment.yaml
│   │   ├── flask_wsgi_svc.yaml
│   │   ├── jsonschema.yaml
│   │   ├── nginx_cm.yaml
│   │   ├── nginx_deployment.yaml
│   │   ├── nginx_hpa.yaml
│   │   └── nginx_svc.yaml
│   ├── load_config.py
│   ├── Payment.py
│   ├── rabbitmq_handler.py
│   ├── requirements-test.txt
│   ├── requirements.txt
│   └── tests
│       └── test_flask.py
├── Images
│   └── PaymentSystem.png
├── Postgres
│   └── k8s_files
│       ├── deployment.yaml
│       ├── pvc.yaml
│       └── svc.yaml
├── README.md
├── riskEngine
│   ├── app.py
│   ├── Dockerfile
│   ├── k8s_files
│   │   ├── risk_analysis_cm.yaml
│   │   ├── risk_engine_cm.yaml
│   │   ├── risk_engine_deployment.yaml
│   │   ├── risk_engine_hpa.yaml
│   │   └── risk_engine_secrets.yaml
│   ├── load_config.py
│   ├── requirements.txt
│   ├── RiskAnalysis.py
│   └── RiskEngine.py
├── SparkQ6
│   ├── SparkQ6.html
│   └── SparkQ6.ipynb
└── tree.txt

12 directories, 56 files
```
