import collections
import random
from dataclasses import dataclass
from typing import List, Deque, Optional, Tuple

@dataclass
class Request:
    id: int
    arrival_time: int
    service_start_time: int
    service_duration: int

class Server:
    def __init__(self, server_id: int, service_rate: float, max_queue_size: int):
            self.id = server_id
            self.service_rate = service_rate  # Mu
            self.max_queue_size = max_queue_size  # Q_i
            
            # State
            self.is_busy: bool = False
            self.queue: Deque[Request] = collections.deque()
            self.current_request: Optional[Request] = None

    def can_accept(self) -> bool:
        """
        Checks if the server can accept a new request.
        A server rejects only if it is BUSY AND its Queue is FULL.
        """
        if not self.is_busy:
            return True
        
        # [cite_start]Note: max_queue_size excludes the one in service [cite: 37]
        return len(self.queue) < self.max_queue_size

    def add_request(self, req: Request) -> bool:
        """
        Tries to accept the request.
        Returns True if accepted (either served or queued).
        Returns False if dropped (full).
        """
        # Case 1: Server is Idle -> Goes directly to service
        if not self.is_busy:
            self.is_busy = True
            self.current_request = req
            return True # Accepted (Immediate Service)
            
        # Case 2: Server Busy, but Queue has space
        if len(self.queue) < self.max_queue_size:
            self.queue.append(req)
            return True # Accepted (Queued)
            
        # Case 3: Full
        return False # Dropped
            
class LoadBalancer:
    def __init__(self, servers: List[Server], probabilities: List[float]):
        self.servers = servers
        self.probabilities = probabilities
        
    def assign_request(self, request: Request) -> Tuple[bool, Optional[Server]]:
        """
        1. Selects a server based on weighted probability P_i.
        2. Tries to push the request to that server.
        
        Returns:
            (True, server_obj) if accepted.
            (False, None) if dropped.
        """
        selected_server = random.choices(self.servers, self.probabilities, k=1)[0]
        accepted = selected_server.add_request(request)
    
        if accepted:
            return True, selected_server
        else:
            return False, None