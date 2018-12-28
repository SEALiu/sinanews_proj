from celery import Celery

app = Celery('celery_app')
app.config_from_object('celery_app.celeryconfig')

# This tells celery to start every task with a clean slate,
# therefore every task will be started in a new process and
# the ReactorNotRestartable problem won't occur.
app.conf.update(
    worker_max_tasks_per_child=1,
    broker_pool_limit=None
)
