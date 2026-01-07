from enum import Enum
from dataclasses import dataclass
from typing import Any

class EventType(Enum):
    ARRIVAL = 1,
    DEPARTURE = 2,
    STOP = 3

@dataclass
class Event:
    time: float
    event_type: EventType
    
    # The 'payload' carries the data needed to process the event.
    # For ARRIVAL: It might be None (or the new Request).
    # For DEPARTURE: It is the Request object that is finishing.
    payload: Any = None

    # Used only for DEPARTURE events to identify which server is freeing up.
    # Default is -1 to indicate 'not applicable' for Arrivals.
    server_index: int = -1

    def __lt__(self, other):
        return self.time < other.time

