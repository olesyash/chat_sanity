import re
from typing import List, Dict, Any
from utils.utils import rtl

def parse_whatsapp_chat(file_path: str, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """Parse a WhatsApp-exported chat text file into a list of messages.

    Expected message start format (single line):
        8/31/25, 17:13 - Name: Message text

    Messages that span multiple lines will be concatenated to the last message.

    Returns a list of dictionaries with keys: 'date', 'time', 'author', 'text'.
    """

    # Pattern with author: 8/31/25, 17:13 - Name: Text
    message_pattern = re.compile(
        r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}) - (.*?): (.*)$"
    )

    # Pattern without author (system messages): 8/31/25, 17:13 - Message text
    system_pattern = re.compile(
        r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}) - (.*)$"
    )

    messages: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None

    with open(file_path, "r", encoding=encoding) as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")

            if not line.strip():
                # Skip completely empty lines
                continue

            match = message_pattern.match(line)
            system_match = None if match else system_pattern.match(line)

            if match or system_match:
                # Start of a new message
                if current is not None:
                    messages.append(current)

                if match:
                    date, time_, author, text = match.groups()
                else:
                    date, time_, text = system_match.groups()  # type: ignore[union-attr]
                    author = None

                current = {
                    "date": date,
                    "time": time_,
                    "author": author,
                    "text": text.strip(),
                }
            else:
                # Continuation of the previous message (multi-line message)
                if current is not None:
                    current["text"] += "\n" + line
                else:
                    # If for some reason the file starts with a continuation line,
                    # treat it as a system message without date/time.
                    current = {
                        "date": None,
                        "time": None,
                        "author": None,
                        "text": line,
                    }

    if current is not None:
        messages.append(current)

    return messages

messages = parse_whatsapp_chat(r"C:\olesya\ChatSanity\data\WhatsApp Chat with גן גפן תשפ_ו\WhatsApp Chat with גן גפן תשפו.txt")
for message in messages[:10]:
    print(rtl(message['text']))