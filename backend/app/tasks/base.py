import logging

from celery import Task


logger = logging.getLogger(__name__)


class LoggedTask(Task):
    abstract = True

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(
            "celery_task_succeeded task_name=%s task_id=%s args=%s",
            self.name,
            task_id,
            args,
        )
        super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            "celery_task_failed task_name=%s task_id=%s args=%s error=%s",
            self.name,
            task_id,
            args,
            exc,
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(
            "celery_task_retry task_name=%s task_id=%s args=%s error=%s",
            self.name,
            task_id,
            args,
            exc,
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)
