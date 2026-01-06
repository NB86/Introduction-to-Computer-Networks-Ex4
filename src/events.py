from enum import Enum

class EventType(Enum):
    ARRIVAL = 1,
    DEPARTURE = 2,
    STOP = 3

class Event:
    def __init__(self, time, priority, event_type, payload):
        self.time = time
        self.priority = priority
        self.event_type = event_type
        self.payload = payload

    def __lt__(self, other):
        if self.time == other.time:
            return self.priority < other.priority
        return self.time < other.time

    def __repr__(self):
        return f"Event(time={self.time}, priority={self.priority}, event_type={self.event_type}, payload={self.payload})" 