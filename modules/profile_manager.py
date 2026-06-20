"""
Personal profile storage for the assistant.
"""

import json
import os
from typing import Dict, List


class ProfileManager:
    """Store and retrieve personal profile information locally."""

    def __init__(self, storage_path: str = None):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.storage_path = storage_path or os.path.join(project_root, "data", "profile.json")
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def remember_fact(self, fact: str):
        profile = self.load_profile()
        facts = profile.setdefault("facts", [])
        if fact not in facts:
            facts.append(fact)
            self._save_profile(profile)
        return facts

    def set_field(self, field: str, value: str):
        profile = self.load_profile()
        profile.setdefault("details", {})[field.strip().lower()] = value.strip()
        self._save_profile(profile)
        return profile

    def set_social(self, platform_name: str, value: str):
        profile = self.load_profile()
        profile.setdefault("social", {})[platform_name.strip().lower()] = value.strip()
        self._save_profile(profile)
        return profile

    def add_project(self, project_name: str):
        profile = self.load_profile()
        projects = profile.setdefault("projects", [])
        if project_name not in projects:
            projects.append(project_name)
            self._save_profile(profile)
        return projects

    def list_projects(self) -> List[str]:
        return self.load_profile().get("projects", [])

    def load_profile(self) -> Dict:
        if not os.path.exists(self.storage_path):
            return {"details": {}, "facts": [], "social": {}, "projects": []}
        with open(self.storage_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def format_profile(self) -> str:
        profile = self.load_profile()
        lines: List[str] = ["Profile:"]

        details = profile.get("details", {})
        facts = profile.get("facts", [])
        social = profile.get("social", {})
        projects = profile.get("projects", [])

        if details:
            lines.append("Details:")
            for key, value in sorted(details.items()):
                lines.append(f"- {key}: {value}")
        if facts:
            lines.append("Facts:")
            for fact in facts:
                lines.append(f"- {fact}")
        if social:
            lines.append("Social:")
            for key, value in sorted(social.items()):
                lines.append(f"- {key}: {value}")
        if projects:
            lines.append("Projects:")
            for project in projects:
                lines.append(f"- {project}")
        if len(lines) == 1:
            lines.append("No profile saved yet.")
        return "\n".join(lines)

    def profile_context(self) -> str:
        return json.dumps(self.load_profile(), ensure_ascii=True)

    def _save_profile(self, profile: Dict):
        with open(self.storage_path, "w", encoding="utf-8") as handle:
            json.dump(profile, handle, indent=2, ensure_ascii=True)
