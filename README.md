# Employees CRUD with Django – DevOps Re-exam

This is my project for the IT Security Management & DevOps re-exam. I started with a simple Employees CRUD app in Flask, then I rewrote it in Django and connected it to a MySQL database. After that I put it into Docker, ran it with Docker Compose, deployed it on Kubernetes with Minikube, and in the end I load-tested it with k6.

## Tools and versions I used

| Part | What I used |
| --- | --- |
| First app | Flask 3.1 (data only in memory) |
| Backend | Django 5.2.17 (LTS), Python 3.12 in the container |
| App server | Gunicorn 26.2.0 |
| Database | MySQL 9.7 (official Docker image), mysqlclient 2.3.0 |
| Containers | Docker (multi-stage build) and Docker Compose |
| Kubernetes | Minikube v1.38.1, Kubernetes v1.35.1, Docker driver |
| Load test | k6 |

## How the repo is organised

```
django-crud-devops/
├── flask-app/                  # my first Flask version
├── django-app/
│   ├── config/                 # Django settings, urls, wsgi
│   ├── employees/              # model, views, urls, migrations
│   ├── Dockerfile              # multi-stage build
│   ├── docker-compose.yml      # Django + MySQL
│   ├── requirements.txt
│   └── manage.py
├── k8s/
│   ├── django-deployment.yaml  # Django Deployment
│   ├── django-config.yaml      # ConfigMap
│   ├── service.yaml            # NodePort Service for Django
│   ├── mysql-deployment.yaml   # MySQL Deployment
│   ├── mysql-volume.yaml       # PersistentVolumeClaim (1Gi)
│   └── mysql-service.yaml      # ClusterIP Service for MySQL
├── load-test/
│   └── virtualusers-load-test.js
└── README.md
```

I didn't upload my `.env` file or `k8s/secret.yaml`, because they have my passwords in them.

## Endpoints

| Method | Endpoint | What it does |
| --- | --- | --- |
| GET | `/health` | checks if the app is running, returns "healthy" |
| GET | `/employees` | shows all employees |
| GET | `/employees/<id>` | shows one employee (404 if it doesn't exist) |
| POST | `/employees` | adds a new employee (201, or 400 if a field is missing) |
| PUT | `/employees/<id>` | updates an employee |
| DELETE | `/employees/<id>` | deletes an employee |

## What you need

You need Docker Desktop, Minikube, kubectl and k6 installed.

## About my Dockerfile

My Dockerfile has two stages:

1. **Build stage** (`python:3.12`): here I install everything from `requirements.txt`. I need the full Python image for this, because mysqlclient has to be compiled and the slim image doesn't have the tools for that.
2. **Run stage** (`python:3.12-slim`): this is the smaller image that actually runs the app. In this stage I:
   - install `libmariadb3`, because mysqlclient needs it to run. Without it, `import MySQLdb` failed in the slim image, which is how I found out.
   - copy the app and the installed packages from the build stage
   - create a user called `appuser` and run the app as that user, so it doesn't run as root
   - expose port 8000
   - start the app with Gunicorn instead of Django's development server:
     `gunicorn config.wsgi:application --bind 0.0.0.0:8000`

I also have a `.dockerignore` so that `.venv` and `.env` don't end up inside the image.

## Running it with Docker Compose

First you need a `.env` file inside `django-app/`. Mine looks like this (with my own values):

```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=employeesdb
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=mysql
DB_PORT=3306
```

Then run:

```
cd django-app
docker compose up -d --build
docker compose ps
docker compose exec app python manage.py migrate
```

After a minute, `docker compose ps` should show both services as **healthy**. The app only starts once MySQL's healthcheck passes, because I used `depends_on` with `condition: service_healthy`. Then you can open http://127.0.0.1:8000/health and it should say "healthy".

## Running it on Minikube

```
minikube start --driver=docker
minikube addons enable metrics-server

docker build -t django-employee-app:v2 django-app
minikube image load django-employee-app:v2

kubectl create namespace django-crud-devops
```

Next, make your own `k8s/secret.yaml` (a Secret called `django-secret` in the namespace `django-crud-devops`) with DJANGO_SECRET_KEY, DB_USER and DB_PASSWORD. Then:

```
kubectl apply -f k8s/
kubectl get pods -n django-crud-devops
kubectl exec -it deploy/django-deployment -n django-crud-devops -- python manage.py migrate
minikube service django-service -n django-crud-devops --url
```

I'm on Windows with the Docker driver, so the last command opens a tunnel. The terminal has to stay open while you use the URL.

### My Kubernetes setup

| | Django | MySQL |
| --- | --- | --- |
| Deployment | 1 replica, image `django-employee-app:v2` | 1 replica, `mysql:9.7` |
| Resources | requests 100m CPU / 128Mi, limits 500m CPU / 256Mi | – |
| Probes | readiness and liveness on `/health` | – |
| Config | ConfigMap `django-config` + Secret `django-secret` | same Secret |
| Storage | – | PVC `mysql-volume`, 1Gi |
| Service | NodePort, 8000 → 31783 | ClusterIP, 3306 |

The image is called `v2` because Minikube kept using my old cached `latest` image, so I built it again with a new tag.

## Load test

My k6 script sends `GET /employees` requests with 500 virtual users for 60 seconds, without any pause between requests. Before you run it, change the URL in the script to your current Minikube URL. Then:

```
k6 run load-test/virtualusers-load-test.js
```

To watch CPU and memory while it runs, I used a second terminal:

```
kubectl top pods -n django-crud-devops
```

### What I got

| Metric | 10 users / 10 s | 500 users / 60 s |
| --- | --- | --- |
| Total requests | 192 | 460,229 |
| Error rate | 0.00% | 99.78% |
| Successful requests | 192 | 986 |
| Successful throughput | 18 req/s | about 16 req/s |
| p95 latency (successful) | 707 ms | 19.34 s |
| Django peak CPU / memory | – | 65m / 56Mi |

With 500 users almost everything failed, but CPU and memory were still far below the limits. I think the main reason is that Gunicorn only ran one sync worker, which can only handle one request at a time. If I continue, the first thing I'd try is more workers.

## Testing self-healing

I killed the main process inside the Django container on purpose:

```
kubectl exec <pod-name> -n django-crud-devops -c django-container -- sh -c "kill 1"
kubectl get pods -n django-crud-devops
```

Kubernetes restarted the container by itself, and the restart count went up from 3 to 4.

## Problems I had

| Problem | How I fixed it |
| --- | --- |
| `import MySQLdb` failed in the slim image | installed `libmariadb3` in the run stage |
| The Django container couldn't find MySQL by name | used a named network (Compose does this for you) |
| The Pod kept crashing (CrashLoopBackOff, HTTP 400) | moved ALLOWED_HOSTS to environment variables, with a ConfigMap and Secret |
| Minikube kept using my old image | built it again with a new tag, `v2` |
| I committed `secret.yaml` by mistake | removed it from Git and added it to `.gitignore` |

You can find more details, screenshots and my full analysis in my report.
