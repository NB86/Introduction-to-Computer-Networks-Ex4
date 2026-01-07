
class StatsCollector:
    def __init__(self):
        self.dropped_requests = 0
        self.served_requests = 0
        self.total_wait_time = 0.0
        self.total_service_time = 0.0
        self.last_departure_time: float = 0.0
        self._arrival_counter: int = 0

    def get_next_id(self) -> int:
        """Generates a unique ID for new requests."""
        req_id = self._arrival_counter
        self._arrival_counter += 1
        return req_id

    def log_drop(self):
        """Called when a packet encounters a full queue."""
        self.dropped_requests += 1

    def log_departure(self, wait_time: float, service_time: float, current_time: float):
        """
        Called when a packet finishes service.
        Updates A, Tw sums, Ts sums, and Tend.
        """
        self.served_requests += 1
        self.total_wait_time += wait_time
        self.total_service_time += service_time
        
        # We always update this because time is monotonic. 
        # The last event processed is by definition the latest time.
        self.last_departure_time = current_time

    def print_report(self):
        """
        Calculates averages and prints the final result line.
        Format: A B Tend AvgTw AvgTs
        """
        # Avoid division by zero if no packets were served
        if self.served_requests > 0:
            avg_wait = self.total_wait_time / self.served_requests
            avg_service = self.total_service_time / self.served_requests
        else:
            avg_wait = 0.0
            avg_service = 0.0

        # Print using f-strings for 4 decimal precision 
        # Format required: A B Tend Tw Ts
        print(f"{self.served_requests} "
              f"{self.dropped_requests} "
              f"{self.last_departure_time:.4f} "
              f"{avg_wait:.4f} "
              f"{avg_service:.4f}")