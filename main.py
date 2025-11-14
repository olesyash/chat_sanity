from pydantic_ai import Agent, BinaryContent
from dotenv import load_dotenv
import logfire
from dataclasses import dataclass
from datetime import datetime
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.google import GoogleModel
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from loguru import logger
from pathlib import Path
from utils.utils import rtl

load_dotenv()

# provider = GoogleProvider(vertexai=True, api_key=os.getenv('GOOGLE_API_KEY'))


# logfire.configure()  
# logfire.instrument_pydantic_ai()  
# logfire.instrument_asyncpg()  
model = GoogleModel('gemini-2.5-flash')

# RTL helpers for proper Hebrew rendering in consoles without bidi support
RLI = "\u2067"  # Right-to-Left isolate
PDI = "\u2069"  # Pop directional isolate


@dataclass
class Event(BaseModel):
    kind: Literal['event'] = 'event'
    name: str
    description: str
    date: datetime
    location: str
    original_message: str | None = None

@dataclass
class Task(BaseModel):
    kind: Literal['task'] = 'task'
    name: str
    description: str
    date: datetime
    link: str | None = None
    original_message: str | None = None

@dataclass
class Other(BaseModel):
    kind: Literal['other'] = 'other'
    original_message: str
    reason: str | None = None

# Discriminated union for parsed outputs
Parsed = Annotated[Event | Task | Other, Field(discriminator='kind')]

def parse_event_picture(path: str):
    """Parse an event image file (jpg/png) and return an Event.
    Args:
        path (str): Path to the image file.
    """
    logger.info("parse_event_picture: parsing image at path={}", path)
    with open(path, 'rb') as f:
        image_bytes = f.read()

    agent = Agent(  
    model=model,
    instructions=(
        "Decide whether the image is an event announcement/flyer or not. "
        "If it's an event, return kind='event' with name, description, date, location. "
        "If it's not an event, return kind='other' with original_message set to the image path and a brief reason. "
        "If in Hebrew, do not translate and do not mix English and Hebrew."
    ),
    output_type=Parsed
    )
    result = agent.run_sync([BinaryContent(image_bytes, media_type='image/jpeg')])
    out = result.output
    # Ensure original_message for 'other' and 'event' carries source path
    if getattr(out, 'original_message', None) is None:
        try:
            out.original_message = path
        except Exception:
            pass
    if getattr(out, 'kind', None) == 'event':
        logger.info("parse_event_picture: event name='{}' date={} location='{}'", getattr(out, 'name', None), getattr(out, 'date', None), getattr(out, 'location', None))
    else:
        logger.info("parse_event_picture: other reason='{}'", getattr(out, 'reason', None))
    return out  


def parse_text(text: str):
    """Parse free text into Event or Task; if neither, return Other.
    """
    logger.info("parse_text: parsing text (len={})", len(text) if text else 0)
    agent = Agent(  
    model=model,
    instructions=(
        "Decide whether the input describes an event or a task. "
        "Return a JSON object with a 'kind' field set to 'event' or 'task'. "
        "If it's an event, include: name, description, date, location. "
        "If it's a task, include: name, description, date, link. "
        "If neither, return kind='other' with original_message and a brief reason. "
        "Set original_message to the raw input text. "
        "If in Hebrew, do not translate and do not mix English and Hebrew."
    ),
    output_type=Parsed
    )
    result = agent.run_sync(text or "")
    out = result.output
    # Ensure original_message is set even if model omits it
    if getattr(out, 'original_message', None) is None:
        try:
            out.original_message = text
        except Exception:
            pass
    logger.info("parse_text: kind={} name='{}' date={}", getattr(out, 'kind', None), getattr(out, 'name', None), getattr(out, 'date', None))
    return out


def route_and_parse(user_input: str) -> Parsed:
    """Pure-Python router: if input is an existing image path -> parse_event_picture; else -> parse_text.
    Returns Event | Task | Other.
    """
    logger.info("route_and_parse: routing input='{}'", user_input)
    p = None
    try:
        p = Path(user_input).expanduser()
    except Exception:
        p = None
    if p and p.exists() and p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}:
        try:
            out = parse_event_picture(str(p))
            logger.info("route_and_parse: image -> event name='{}'", getattr(out, 'name', None))
            return out
        except FileNotFoundError:
            logger.info("route_and_parse: image path not found -> other")
            return Other(kind='other', original_message=user_input, reason='image path not found')
        except Exception as e:
            logger.info("route_and_parse: image parse error -> other: {}", e)
            return Other(kind='other', original_message=user_input, reason=f'image parse error: {e}')
    # default: treat as text
    out = parse_text(user_input)
    logger.info("route_and_parse: text parsed kind={} name='{}'", getattr(out, 'kind', None), getattr(out, 'name', None))
    return out


event_or_task = route_and_parse(r'data\\event1.jpg')

if getattr(event_or_task, 'kind', None) == 'event':
    print(rtl(event_or_task.name))
    print(rtl(event_or_task.description))
    print(event_or_task.date)
    print(rtl(event_or_task.location))
elif getattr(event_or_task, 'kind', None) == 'task':
    print(rtl(event_or_task.name))
    print(rtl(event_or_task.description))
    print(event_or_task.date)
    print(getattr(event_or_task, 'link', None))
else:
    logger.info("router: input is neither event nor task; reason='{}'", getattr(event_or_task, 'reason', None))
    print("OTHER:", getattr(event_or_task, 'reason', None))
