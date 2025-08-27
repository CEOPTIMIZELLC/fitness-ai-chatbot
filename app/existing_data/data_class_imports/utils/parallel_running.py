from app import db
from concurrent.futures import ThreadPoolExecutor, as_completed


def set_up_future_without_args(ex, tasks):
    return [
            ex.submit(ex_task) 
            for ex_task in tasks
        ]


def set_up_future_with_args(ex, tasks, task_args):
    return [
            ex.submit(ex_task, ex_arg) 
            for ex_task, ex_arg in zip(tasks, task_args)
        ]


def run_parallel_queries(tasks, task_args=[]):
    max_workers = len(tasks)

    # Run them concurrently; each thread gets its own Session
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        if task_args:
            futures = set_up_future_with_args(ex, tasks, task_args)
        else:
            futures = set_up_future_without_args(ex, tasks)

        # propagate exceptions if any
        for fut in as_completed(futures):
            fut.result()

    # db.session.commit()
    return None