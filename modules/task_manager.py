"""
Task management with simple JSON persistence.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List


@dataclass
class TaskItem:
    """Persisted task record."""

    title: str
    completed: bool = False
    created_at: str = ""
    completed_at: str = ""


class TaskManager:
    """Create, list, and complete tasks."""

    def __init__(self, storage_path: str = None):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.storage_path = storage_path or os.path.join(project_root, "data", "tasks.json")
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def create_task(self, title: str) -> TaskItem:
        tasks = self._load_tasks()
        normalized = title.strip()
        existing = self._find_task(tasks, normalized)
        if existing:
            return existing

        task = TaskItem(
            title=normalized,
            completed=False,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        tasks.append(task)
        self._save_tasks(tasks)
        return task

    def list_tasks(self) -> List[TaskItem]:
        return self._load_tasks()

    def complete_task(self, title: str) -> TaskItem | None:
        tasks = self._load_tasks()
        task = self._find_task(tasks, title)
        if not task:
            return None

        if not task.completed:
            task.completed = True
            task.completed_at = datetime.now().isoformat(timespec="seconds")
            self._save_tasks(tasks)
        return task

    def _load_tasks(self) -> List[TaskItem]:
        if not os.path.exists(self.storage_path):
            return []

        with open(self.storage_path, "r", encoding="utf-8") as handle:
            raw_tasks = json.load(handle)
        return [TaskItem(**item) for item in raw_tasks]

    def _save_tasks(self, tasks: List[TaskItem]):
        with open(self.storage_path, "w", encoding="utf-8") as handle:
            json.dump([asdict(task) for task in tasks], handle, indent=2)

    @staticmethod
    def _find_task(tasks: List[TaskItem], title: str) -> TaskItem | None:
        normalized = title.strip().lower()
        for task in tasks:
            if task.title.strip().lower() == normalized:
                return task
        return None
