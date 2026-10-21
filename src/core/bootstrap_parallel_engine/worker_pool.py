"""Concurrent task execution pool for the parallel bootstrap engine."""

from __future__ import annotations

import concurrent.futures
import threading
import time
from typing import Optional

from .graph import resolve_dag_dependencies
from .models import BootstrapContext, BootstrapTask, TaskStatus, TaskTiming


def execute_tasks_parallel(
    tasks: list[BootstrapTask],
    context: BootstrapContext,
) -> bool:
    """Dynamically schedule and execute tasks via ThreadPoolExecutor according to DAG."""
    resolve_dag_dependencies(tasks)

    task_map = {t.id: t for t in tasks}
    completed_tasks: set[str] = set()
    failed_tasks: set[str] = set()
    submitted_tasks: set[str] = set()
    active_futures: dict[concurrent.futures.Future, str] = {}

    lock = threading.Lock()
    has_fatal_failure = False

    def run_single_task(task: BootstrapTask) -> tuple[str, bool, Optional[str]]:
        worker_id = threading.current_thread().name
        start_time = time.time()
        timing = TaskTiming(
            task_id=task.id,
            name=task.name,
            start_time=start_time,
            worker_id=worker_id,
            status=TaskStatus.RUNNING,
        )
        with context.lock:
            context.task_timings[task.id] = timing

        err: Optional[str] = None
        success = True
        try:
            task.action(context)
            timing.status = TaskStatus.COMPLETED
        except Exception as exc:
            err = str(exc)
            success = False
            timing.status = TaskStatus.FAILED
            timing.error = err
            with context.lock:
                context.errors.append(f"Task '{task.id}' failed: {err}")
        finally:
            end_time = time.time()
            timing.end_time = end_time
            timing.duration_ms = round((end_time - start_time) * 1000, 2)

        return task.id, success, err

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max(1, context.workers)
    ) as executor:

        def submit_ready_tasks() -> None:
            nonlocal has_fatal_failure
            if has_fatal_failure:
                return
            for t in tasks:
                if t.id not in submitted_tasks:
                    if all(dep in completed_tasks for dep in t.dependencies):
                        submitted_tasks.add(t.id)
                        fut = executor.submit(run_single_task, t)
                        active_futures[fut] = t.id

        with lock:
            submit_ready_tasks()

        while True:
            with lock:
                if not active_futures:
                    break
                futures_to_wait = list(active_futures.keys())

            done, _ = concurrent.futures.wait(
                futures_to_wait,
                return_when=concurrent.futures.FIRST_COMPLETED,
            )

            with lock:
                for fut in done:
                    if fut in active_futures:
                        tid = active_futures.pop(fut)
                        task = task_map[tid]
                        try:
                            _, success, _ = fut.result()
                        except Exception:
                            success = False

                        if success:
                            completed_tasks.add(tid)
                        else:
                            failed_tasks.add(tid)
                            if not task.optional:
                                has_fatal_failure = True
                                for pending_fut in list(active_futures.keys()):
                                    pending_fut.cancel()
                                break

                if not has_fatal_failure:
                    submit_ready_tasks()
                else:
                    break

        for t in tasks:
            with context.lock:
                if t.id not in context.task_timings:
                    context.task_timings[t.id] = TaskTiming(
                        task_id=t.id,
                        name=t.name,
                        start_time=0.0,
                        end_time=0.0,
                        duration_ms=0.0,
                        status=TaskStatus.SKIPPED,
                    )
                elif t.id not in completed_tasks and t.id not in failed_tasks:
                    context.task_timings[t.id].status = TaskStatus.SKIPPED

    return not has_fatal_failure
