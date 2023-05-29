cd ../flaskApp
# re-build
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 850414232980.dkr.ecr.eu-central-1.amazonaws.com
docker build -t 850414232980.dkr.ecr.eu-central-1.amazonaws.com/myrepo:wsgi-flask-python-1.0 .
docker push 850414232980.dkr.ecr.eu-central-1.amazonaws.com/myrepo:wsgi-flask-python-1.0