import os
import sys
import traceback

workers = 4
worker_connections = 256
errorlog = "/home/vcap/logs/gunicorn_error.log"
bind = "0.0.0.0:{}".format(os.getenv("PORT", "5000"))


def on_starting(server):
    server.log.info("Starting Team Metrics")


def worker_abort(worker):
    worker.log.info("worker received ABORT {}".format(worker.pid))
    for thread_id, stack in sys._current_frames().items():
        worker.log.error(''.join(traceback.format_stack(stack)))


def on_exit(server):
    server.log.info("Stopping Team Metrics")


def worker_int(worker):
    worker.log.info("worker: received SIGINT {}".format(worker.pid))
