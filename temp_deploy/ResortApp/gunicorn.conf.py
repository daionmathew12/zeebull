# Gunicorn configuration file for Resort Management System
# Production deployment on Vultr

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:8011"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 120  # Increased timeout for slower operations
graceful_timeout = 30  # Graceful shutdown timeout
keepalive = 5  # Increased keepalive for better connection reuse

# Logging
accesslog = "/var/log/orchid/access.log"
errorlog = "/var/log/orchid/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "orchid_management"

# Server mechanics
daemon = False
pidfile = None  # Let systemd manage the PID
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (if using HTTPS directly through Gunicorn)
# keyfile = "/etc/letsencrypt/live/teqmates.com/privkey.pem"
# certfile = "/etc/letsencrypt/live/teqmates.com/fullchain.pem"
# ssl_version = 2
# ciphers = "TLSv1"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Application
pythonpath = "/var/www/resort"
chdir = "/var/www/resort/orchid_production/ResortApp"

# Performance
worker_tmp_dir = "/dev/shm"
max_requests_jitter = 50


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Orchid Resort Management System is ready to serve requests")


def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info("Worker received SIGINT or SIGQUIT")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug("%s %s", req.method, req.path)


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    worker.log.debug("Response status: %s", resp.status)
