import random

@dataclass
class Request:
    arrival_time: int
    service_start_time: int

class Server:
    def __init__(self, max_queue_size: int):
        self.is_busy = False
        self.current_request: Request | None = None
        self.queue: list[Request] = []
        self.max_queue_size = max_queue_size

    def try_queue(self, request: Request) -> bool:
        if len(self.queue) < max_queue_size:
            self.queue.append(request)
            return True
        return False

class LoadBalancer:
    def __init__(self, servers: list[dict[Server, float]]):
        self.servers = servers
        
    def assign_request(self, request: Request) -> bool:
        chosen_server = random.choices(self.servers.keys(), self.servers.values(), k=1)[0]
        if server.try_queue(request):
            return True
        return False 
