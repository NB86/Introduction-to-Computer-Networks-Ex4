from enum import Enum

class EventType(Enum):
    ARRIVAL = 1,
    DEPARTURE = 2,
    STOP = 3

@dataclass
class Event:
        time: int
        priority: int
        event_type: EventType
        payload: dict

    def __lt__(self, other):
        if self.time == other.time:
            return self.priority < other.priority
        return self.time < other.time

