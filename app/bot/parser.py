def parse_command(text: str) -> tuple[str | None, str | None]:
    """
    Parses an incoming WhatsApp message.
    Returns (command, args).
    If it's not a command (doesn't start with /), command is None and args is the full text.
    """
    text = text.strip()
    if not text.startswith("/"):
        return None, text
        
    parts = text.split(" ", 1)
    command = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else None
    
    return command, args
