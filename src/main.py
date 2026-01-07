import sys
from dataclasses import dataclass
from typing import List
import heapq
import random

from events import Event, EventType
from network import Server, LoadBalancer, Request
from stats import StatsCollector

# Input example: 100 3 0.5 0.3 0.2 2.0 5 10 15 1.0 0.5 0.2

@dataclass
class SimulationConfig:
    """Holds the validated configuration for a simulation run."""
    max_time: float      # T
    server_count: int    # M
    probabilities: List[float] # P_i
    arrival_rate: float  # Lambda
    queue_sizes: List[int]     # Q_i
    service_rates: List[float] # Mu_i

def parse_args(args: List[str]) -> SimulationConfig:
    """
    Parses command line arguments according to the spec:
    ./simulator T M P1...PM Lambda Q1...QM Mu1...MuM
    """
    # 1. Basic Safety Check: Do we have enough arguments to even start?
    # We need at least script_name, T, M (3 args minimum)
    if len(args) < 6:
        print("Error: Not enough arguments.")
        print("Usage: ./simulator T M P1...PM Lambda Q1...QM Mu1...MuM")
        sys.exit(1)

    try:
        # 2. Extract Static Heads
        max_time = float(args[1])
        server_count = int(args[2])

        if server_count < 1:
            raise ValueError(f"M must be at least 1, got {server_count}")

        # 3. Calculate Dynamic Offsets
        # The list of Ps starts at index 3 and is M long.
        p_start = 3
        p_end = p_start + server_count
        
        # Lambda is immediately after the Ps
        lambda_index = p_end
        
        # Qs start after Lambda and are M long
        q_start = lambda_index + 1
        q_end = q_start + server_count
        
        # Mus start after Qs and are M long
        mu_start = q_end
        mu_end = mu_start + server_count

        # 4. Verify Total Argument Count
        # Expected length: mu_end (since slices are exclusive, mu_end is the index AFTER the last element)
        if len(args) != mu_end:
            raise ValueError(f"Expected {mu_end - 1} arguments for M={server_count}, but got {len(args) - 1}.")

        # 5. Extract Lists using Slices
        probabilities = [float(x) for x in args[p_start:p_end]]  # P_i
        arrival_rate = float(args[lambda_index])                 # Lambda
        queue_sizes = [int(x) for x in args[q_start:q_end]]      # Q_i
        service_rates = [float(x) for x in args[mu_start:mu_end]] # Mu_i

        # 6. Logical Validation
        # Verify probabilities sum to 1 (with small epsilon for float errors)
        if abs(sum(probabilities) - 1.0) > 1e-5:
             raise ValueError(f"Probabilities must sum to 1. Got sum={sum(probabilities)}")

        # Verify Queue sizes are non-negative
        if any(q < 0 for q in queue_sizes):
            raise ValueError("Queue sizes cannot be negative.")

        return SimulationConfig(
            max_time=max_time,
            server_count=server_count,
            probabilities=probabilities,
            arrival_rate=arrival_rate,
            queue_sizes=queue_sizes,
            service_rates=service_rates
        )

    except ValueError as e:
        print(f"Error parsing arguments: {e}")
        sys.exit(1)
    except IndexError:
        print("Error: Argument list mismatch. Check your M value vs the provided lists.")
        sys.exit(1)

def handle_arrival(event: Event, config, load_balancer, event_queue, stats):
    """
    Generates the NEXT arrival (Self-Scheduling).
    Routes the CURRENT arrival to a server.
    """
    current_time = event.time
    
    # --- Schedule Next Arrival (The Chain Reaction) ---
    # We always schedule the next arrival first to keep the stream alive.
    next_interval = random.expovariate(config.arrival_rate)
    next_arrival_time = current_time + next_interval
    
    # We stop creating NEW arrivals if time exceeds T
    if next_arrival_time < config.max_time:
        next_event = Event(
            time=next_arrival_time,
            event_type=EventType.ARRIVAL,
            payload=None
        )
        heapq.heappush(event_queue, next_event)

    # --- Process Current Request ---
    # Create the request object
    req = Request(id=stats.get_next_id(), arrival_time=current_time, service_start_time=None, service_duration=None)
    
    accepted, server = load_balancer.assign_request(req)
    
    if not accepted:
        stats.log_drop()
        return

    # Case: Accepted
    # Now check: Did it start service IMMEDIATELY?
    # If the server took it and was idle, it is now BUSY and we must schedule its departure.
    # We identify this by checking if the request we just sent is the one currently in service.
    
    if server.current_request == req:
        # It skipped the queue!
        req.service_start_time = current_time # Wait time = 0
        
        # Calculate Service Duration (Exponential)
        service_duration = random.expovariate(server.service_rate)
        req.service_duration = service_duration
        
        departure_time = current_time + service_duration
        
        # Schedule Departure
        dep_event = Event(
            time=departure_time,
            event_type=EventType.DEPARTURE,
            payload=req,
            server_index=server.id
        )
        heapq.heappush(event_queue, dep_event)
        
    # If it went into the queue, we do NOT schedule a departure yet. 
    # It will be scheduled later, when the server finishes the previous job.

def handle_departure(event: Event, load_balancer, event_queue, stats):
    """
    Handles the completion of a request at a specific server.
    """
    current_time = event.time
    
    # 1. Retrieve Context
    # We use the server_index stored in the event to find the right server object
    server = load_balancer.servers[event.server_index]
    finished_req = event.payload
    
    # 2. Update Statistics (for the request that just finished)    
    wait_time = finished_req.service_start_time - finished_req.arrival_time
    service_time = finished_req.service_duration
    
    stats.log_departure(wait_time, service_time, current_time)
    
    # 3. Check for Next Job
    if server.queue:
        # --- SCENARIO A: There is work in the queue ---
        # The server remains BUSY. We immediately pull the next request.
        next_req = server.queue.popleft()
        
        # Update Server State
        server.current_request = next_req
        
        # Mark the start of service for this new request
        next_req.service_start_time = current_time
        
        # Calculate Service Duration (Exponential Randomness)
        # Note: We generate this NOW, as the service actually begins NOW.
        service_duration = random.expovariate(server.service_rate)
        next_req.service_duration = service_duration
        
        # Schedule the FUTURE Departure
        departure_time = current_time + service_duration
        
        new_event = Event(
            time=departure_time,
            event_type=EventType.DEPARTURE,
            payload=next_req,
            server_index=server.id
        )
        heapq.heappush(event_queue, new_event)
        
    else:
        # --- SCENARIO B: The queue is empty ---
        # The server has nothing to do.
        server.is_busy = False
        server.current_request = None

def main():
    config = parse_args(sys.argv)
    servers = [Server(i, config.service_rates[i], config.queue_sizes[i]) for i in range(config.server_count)]
    load_balancer = LoadBalancer(servers, config.probabilities)
    stats = StatsCollector()
    current_time = 0.0
    event_queue = []
    first_interval = random.expovariate(config.arrival_rate)
    first_arrival_time = current_time + first_interval
    
    if first_arrival_time < config.max_time:
        first_event = Event(
            time=first_arrival_time, 
            event_type=EventType.ARRIVAL, 
            payload=None
        )
        heapq.heappush(event_queue, first_event)

    while event_queue:
        current_event = heapq.heappop(event_queue)
        
        # Update the Global Clock
        current_time = current_event.time
        
        if current_event.event_type == EventType.ARRIVAL:
            handle_arrival(current_event, config, load_balancer, event_queue, stats)
            
        elif current_event.event_type == EventType.DEPARTURE:
            handle_departure(current_event, load_balancer, event_queue, stats)

if __name__ == "__main__":
    main()