"""
Task Router Module

Routes tasks to appropriate modules based on intent.
"""

import os
import webbrowser

from modules.excel_generator import create_excel
from modules.presentation_generator import PresentationGenerator, PresentationRequest
from modules.email_assistant import EmailAssistant
from modules.pdf_assistant import summarize_pdf
from modules.profile_manager import ProfileManager
from modules.social_apps import open_social, search_linkedin_jobs
from modules.task_manager import TaskManager
from modules.web_search import answer_from_web
from core.llm_provider import LLMProviderManager
from core.nlu_engine import NLUEngine
from modules.app_control import open_app

# Initialize NLU engine
nlu_engine = NLUEngine()
task_manager = TaskManager()
profile_manager = ProfileManager()


def _safe_filename(text: str, default: str = 'sample') -> str:
    """Create a filesystem-safe filename and ensure .xlsx extension."""
    import re
    if not text:
        base = default
    else:
        base = text.strip().lower()
        # remove common filler words
        base = re.sub(r"\b(of|the|on|in|for|storing|data|file|named|called)\b", " ", base)
        base = re.sub(r'[^\w\s-]', '', base)
        base = re.sub(r'[-\s]+', '_', base).strip('_')
        if not base:
            base = default

    if not base.lower().endswith('.xlsx'):
        base = f"{base}.xlsx"

    return base

def route_task(intent, parsed_command):
    """
    Route the task to the appropriate module.

    Args:
        intent (str): The detected intent.
        parsed_command (dict): Parsed command with 'command' and 'args'.
    """
    # Reconstruct full command for NLU processing
    full_command = parsed_command['command'] + ' ' + ' '.join(parsed_command['args'])
    nlu_result = nlu_engine.process_command(full_command)

    # Show fallback message if any
    if nlu_result.fallback_message:
        print(nlu_result.fallback_message)

    args = parsed_command['args']
    entities = nlu_result.extracted_entities

    if intent == 'create_excel':
        raw_name = entities.get('file_name')
        # Prefer a clean topic as filename when file_name looks like a descriptive phrase
        topic = entities.get('topic')
        if raw_name:
            # If raw_name contains many words and no extension, prefer topic if available
            if ' ' in raw_name and topic:
                filename = _safe_filename(topic, default='data')
            else:
                filename = _safe_filename(raw_name, default='data')
        else:
            filename = _safe_filename(topic or 'sample', default='sample')

        create_excel(filename, topic=topic)
        print("Excel file created successfully.")
    elif intent == 'create_presentation':
        topic = entities.get('topic', 'general topic')
        slide_count = int(entities.get('slide_count', 5))
        request = PresentationRequest(topic=topic, slide_count=slide_count)
        generator = PresentationGenerator()
        try:
            output_path = generator.generate_presentation(request)
            print(f"Presentation created successfully: {output_path}")
        except Exception as e:
            print(f"Error creating presentation: {e}")
    elif intent == 'open_app':
        app_name = entities.get('app_name', ' '.join(args[1:]) if len(args) > 1 else '')
        open_app(app_name)
    elif intent == 'draft_email':
        email_type = entities.get('topic', 'general')
        recipient = entities.get('recipient', 'colleague')
        tone = 'formal'  # Could be extracted from entities if needed
        purpose = entities.get('subject', entities.get('topic', ''))
        assistant = EmailAssistant()
        try:
            draft = assistant.draft_email(email_type, recipient, tone, purpose)
            filepath = assistant.save_draft(draft)
            print(f"Email draft created successfully: {filepath}")
            print(f"Subject: {draft.subject}")
        except Exception as e:
            print(f"Error drafting email: {e}")
    elif intent == 'create_note':
        topic = entities.get('topic', 'general note')
        print(f"Creating note about {topic}...")
        # Placeholder - implement note creation
    elif intent == 'create_task':
        task_title = entities.get('task_title', entities.get('topic', 'new task'))
        task = task_manager.create_task(task_title)
        print(f"Task saved: {task.title}")
        print(f"Status: {'completed' if task.completed else 'pending'}")
    elif intent == 'list_tasks':
        tasks = task_manager.list_tasks()
        if not tasks:
            print("No tasks found.")
        else:
            print("Tasks:")
            for idx, task in enumerate(tasks, start=1):
                status = 'done' if task.completed else 'pending'
                print(f"{idx}. [{status}] {task.title}")
    elif intent == 'complete_task':
        task_title = entities.get('task_title', entities.get('topic', 'task'))
        task = task_manager.complete_task(task_title)
        if task:
            print(f"Task completed: {task.title}")
        else:
            print(f"Task not found: {task_title}")
    elif intent == 'open_website':
        website = entities.get('app_name', ' '.join(args))
        target = website.strip()
        if target and not target.startswith(('http://', 'https://')):
            target = f"https://{target}"
        webbrowser.open(target)
        print(f"Opening website: {target}")
    elif intent == 'file_search':
        query = entities.get('topic', ' '.join(args))
        matches = _search_local_files(query)
        if matches:
            print("Matching files:")
            for match in matches[:10]:
                print(match)
        else:
            print(f"No files found for: {query}")
    elif intent == 'file_organize':
        folder = entities.get('file_name', 'downloads')
        print(f"Organizing folder: {folder}...")
        # Placeholder - implement file organization
    elif intent == 'ask_assistant':
        manager = LLMProviderManager()
        profile_context = profile_manager.profile_context()
        answer = manager.generate_assistant_answer(
            f"User profile context: {profile_context}\nUser request: {full_command.strip()}"
        )
        print(answer.answer)
        if answer.suggested_actions:
            print("Suggested actions:")
            for action in answer.suggested_actions:
                print(f"- {action}")
    elif intent == 'web_search':
        query = entities.get('topic', full_command.strip())
        print(answer_from_web(query))
    elif intent == 'summarize_pdf':
        pdf_path = entities.get('file_name', '').strip()
        print(summarize_pdf(pdf_path))
    elif intent == 'remember_profile':
        raw_fact = entities.get('profile_fact', '').strip()
        if not raw_fact:
            print("Please provide profile information to save.")
        elif raw_fact.lower().startswith(('linkedin ', 'whatsapp ', 'github ', 'instagram ')):
            platform_name, value = raw_fact.split(' ', 1)
            profile_manager.set_social(platform_name, value)
            print(f"Saved {platform_name} profile.")
        elif ':' in raw_fact:
            field, value = raw_fact.split(':', 1)
            profile_manager.set_field(field, value)
            print(f"Saved profile field: {field.strip()}")
        else:
            profile_manager.remember_fact(raw_fact)
            print("Saved personal fact.")
    elif intent == 'show_profile':
        print(profile_manager.format_profile())
    elif intent == 'add_project':
        project_name = entities.get('project_name', entities.get('topic', 'new project'))
        profile_manager.add_project(project_name)
        print(f"Project added: {project_name}")
    elif intent == 'list_projects':
        projects = profile_manager.list_projects()
        if not projects:
            print("No projects saved yet.")
        else:
            print("Projects:")
            for project in projects:
                print(f"- {project}")
    elif intent == 'open_social':
        target = entities.get('app_name', entities.get('topic', ''))
        print(open_social(target))
    elif intent == 'linkedin_jobs':
        query = entities.get('topic', 'software engineer')
        print(search_linkedin_jobs(query))
    else:
        print("Intent not recognized or not yet implemented.")


def _search_local_files(query: str):
    """Find matching files under the project workspace."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    query_words = [word for word in query.lower().split() if word]
    matches = []
    ignored_dirs = {'.git', '.venv', '__pycache__', '.agents', '.codex'}

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [directory for directory in dirs if directory not in ignored_dirs]
        for name in files:
            path = os.path.join(root, name)
            relative_path = os.path.relpath(path, project_root)
            haystack = relative_path.lower()
            if all(word in haystack for word in query_words):
                matches.append(relative_path)

    return sorted(matches)
