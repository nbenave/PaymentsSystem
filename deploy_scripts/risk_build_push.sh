cd ../riskEngine
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 850414232980.dkr.ecr.eu-central-1.amazonaws.com
docker build -t 850414232980.dkr.ecr.eu-central-1.amazonaws.com/myrepo:risk-engine-app-1.0 .
docker push 850414232980.dkr.ecr.eu-central-1.amazonaws.com/myrepo:risk-engine-app-1.0
