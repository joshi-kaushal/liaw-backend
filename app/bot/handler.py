import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.parser import parse_command
from app.models.user import User
from app.schemas.task import TaskCreate, TaskFilterParams
from app.services import task_service, auth_service
from app.services.whatsapp_service import send_text_message

logger = logging.getLogger(__name__)

HELP_TEXT = """
*Live in a Week Bot* 🗓️

Available commands:
• `/today` - Show today's tasks
• `/week` - Show pending tasks for this week
• `/add <task>` - Add a new task for today
• `/done <number>` - Complete a task
• `/delete <number>` - Delete a task
• `/otp` - Get a login code for the extension
""".strip()


async def handle_whatsapp_message(db: AsyncSession, phone_number: str, message_text: str):
    """Entry point for handling an incoming WhatsApp message."""
    # Ensure phone number has + prefix
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    command, args = parse_command(message_text)

    # Find user
    user = await auth_service.get_or_create_user(db, phone_number)

    # Handle /otp command (Brilliant workaround!)
    if command == "/otp":
        code = await auth_service.create_otp(db, user.id)
        reply = f"🔐 Your Live in a Week verification code is *{code}*.\n\nValid for 5 minutes. Enter this in the browser extension to log in."
        await send_text_message(phone_number, reply)
        return

    # For all other commands, if user isn't verified (hasn't logged into extension at least once)
    # We could restrict them, but since this bot IS the source of truth, we can let them use it.
    
    if command == "/help" or command == "/start":
        await send_text_message(phone_number, HELP_TEXT)
        return

    if command == "/today":
        await _handle_today(db, user.id, phone_number)
        return

    if command == "/week":
        await _handle_week(db, user.id, phone_number)
        return

    if command == "/add":
        if not args:
            await send_text_message(phone_number, "❌ Please provide a task title. Example: `/add Buy groceries`")
            return
        await _handle_add(db, user.id, phone_number, args)
        return
        
    if command == "/done":
        if not args or not args.isdigit():
            await send_text_message(phone_number, "❌ Please provide the task number. Example: `/done 1`")
            return
        await _handle_done(db, user.id, phone_number, int(args))
        return

    if command == "/delete":
        if not args or not args.isdigit():
            await send_text_message(phone_number, "❌ Please provide the task number. Example: `/delete 1`")
            return
        await _handle_delete(db, user.id, phone_number, int(args))
        return

    # Default fallback
    if command:
        await send_text_message(phone_number, f"❓ Unknown command '{command}'. Send `/help` to see available commands.")
    else:
        # If it's just text, treat it as /add
        await _handle_add(db, user.id, phone_number, args)


async def _handle_today(db: AsyncSession, user_id, phone_number: str):
    today = datetime.now(timezone.utc).date()
    filters = TaskFilterParams(start_date=today, end_date=today, status="pending")
    tasks = await task_service.get_tasks(db, user_id, filters)
    
    if not tasks:
        await send_text_message(phone_number, "🎉 You have no pending tasks for today! Enjoy your day.")
        return

    lines = ["📋 *Today's Tasks*:"]
    for i, t in enumerate(tasks, 1):
        lines.append(f"{i}. [ ] {t.title}")
    
    await send_text_message(phone_number, "\n".join(lines))


async def _handle_week(db: AsyncSession, user_id, phone_number: str):
    today = datetime.now(timezone.utc).date()
    # Calculate days to Sunday (6 = Sunday in Python, but let's just do next 7 days for simplicity)
    end_of_week = today + timedelta(days=7)
    
    filters = TaskFilterParams(start_date=today, end_date=end_of_week, status="pending")
    tasks = await task_service.get_tasks(db, user_id, filters)
    
    if not tasks:
        await send_text_message(phone_number, "🎉 You have no pending tasks for the next 7 days!")
        return

    lines = ["📋 *This Week's Pending Tasks*:"]
    for i, t in enumerate(tasks, 1):
        due = t.due_date.strftime("%a") if t.due_date else "Anyday"
        lines.append(f"{i}. [ ] {t.title} ({due})")
    
    await send_text_message(phone_number, "\n".join(lines))


async def _handle_add(db: AsyncSession, user_id, phone_number: str, title: str):
    task_in = TaskCreate(
        title=title,
        due_date=datetime.now(timezone.utc).date(),
    )
    task = await task_service.create_task(db, user_id, task_in)
    await send_text_message(phone_number, f"✅ Added: *{task.title}*")


async def _handle_done(db: AsyncSession, user_id, phone_number: str, index: int):
    # Fetch today's tasks to map index to task ID
    today = datetime.now(timezone.utc).date()
    # Let's just fetch all pending tasks to be safe, ordered by creation
    filters = TaskFilterParams(status="pending")
    tasks = await task_service.get_tasks(db, user_id, filters)
    
    if not tasks or index < 1 or index > len(tasks):
        await send_text_message(phone_number, "❌ Invalid task number. Run `/today` or `/week` to see the numbers.")
        return
        
    task_to_complete = tasks[index - 1]
    
    # We need to use TaskUpdate, but it requires 'version'
    from app.schemas.task import TaskUpdate
    update_data = TaskUpdate(
        status="completed",
        completed_at=datetime.now(timezone.utc),
        version=task_to_complete.version
    )
    
    await task_service.update_task(db, user_id, task_to_complete.id, update_data)
    await send_text_message(phone_number, f"☑️ Completed: ~{task_to_complete.title}~")


async def _handle_delete(db: AsyncSession, user_id, phone_number: str, index: int):
    filters = TaskFilterParams(status="pending")
    tasks = await task_service.get_tasks(db, user_id, filters)
    
    if not tasks or index < 1 or index > len(tasks):
        await send_text_message(phone_number, "❌ Invalid task number.")
        return
        
    task_to_delete = tasks[index - 1]
    await task_service.delete_task(db, user_id, task_to_delete.id)
    await send_text_message(phone_number, f"🗑️ Deleted: *{task_to_delete.title}*")
