"""
Task Router Module

Routes tasks to appropriate modules based on intent.
"""

from modules.excel_generator import create_excel
from modules.presentation_generator import PresentationGenerator, PresentationRequest
from modules.email_assistant import EmailAssistant
from core.nlu_engine import NLUEngine
from modules.app_control import open_app

# Initialize NLU engine
nlu_engine = NLUEngine()


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

        create_excel(filename)
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
        print(f"Creating task: {task_title}...")
        # Placeholder - implement task creation
    elif intent == 'list_tasks':
        print("Listing tasks...")
        # Placeholder - implement task listing
    elif intent == 'complete_task':
        task_title = entities.get('task_title', entities.get('topic', 'task'))
        print(f"Marking task complete: {task_title}...")
        # Placeholder - implement task completion
    elif intent == 'open_website':
        website = entities.get('app_name', ' '.join(args))
        print(f"Opening website: {website}...")
        # Placeholder - implement website opening
    elif intent == 'file_search':
        query = entities.get('topic', ' '.join(args))
        print(f"Searching for files: {query}...")
        # Placeholder - implement file search
    elif intent == 'file_organize':
        folder = entities.get('file_name', 'downloads')
        print(f"Organizing folder: {folder}...")
        # Placeholder - implement file organization
    else:
        print("Intent not recognized or not yet implemented.")