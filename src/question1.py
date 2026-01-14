import random
import heapq
import sys
import csv

def main(arrival_rate, service_rate, simulation_time, max_queue_size):
    # Events
    ARRIVAL = 1
    DEPARTURE = 2

    # State variables
    current_time = 0.0
    queue = []
    server_busy = False
    event_list = []

    # Statistics
    total_wait_time = 0.0
    num_customers_served = 0
    num_customers_rejected = 0
    num_customers_arrived = 0

    # Schedule the first arrival
    heapq.heappush(event_list, (random.expovariate(arrival_rate), ARRIVAL))

    while current_time < simulation_time:
        event_time, event_type = heapq.heappop(event_list)
        current_time = event_time
        
        if event_type == ARRIVAL:
            num_customers_arrived += 1
            if not server_busy:
                server_busy = True
                service_time = random.expovariate(service_rate)
                heapq.heappush(event_list, (current_time + service_time, DEPARTURE))
            else:
                if len(queue) < max_queue_size:
                    queue.append(current_time)
                else:
                    num_customers_rejected += 1
            next_arrival = current_time + random.expovariate(arrival_rate)
            heapq.heappush(event_list, (next_arrival, ARRIVAL))
        elif event_type == DEPARTURE:
            num_customers_served += 1
            if queue:
                arrival_time = queue.pop(0)
                wait_time = current_time - arrival_time
                total_wait_time += wait_time
                service_time = random.expovariate(service_rate)
                heapq.heappush(event_list, (current_time + service_time, DEPARTURE))
            else:
                server_busy = False

    # Count customers still in queue as not served
    num_not_served = num_customers_rejected + len(queue)

    # Results
    avg_wait_time = total_wait_time / num_customers_served if num_customers_served > 0 else 0
    
    return {
        "num_customers_served": num_customers_served,
        "num_customers_not_served": num_not_served,
        "average_wait_time": avg_wait_time
    }

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Error: Invalid number of arguments")
        print("Usage: python question1.py <arrival_rate> <service_rate> <max_queue_size> <num_runs>")
        sys.exit(1)
    
    try:
        arrival_rate = float(sys.argv[1])
        service_rate = float(sys.argv[2])
        max_queue_size = int(sys.argv[3])
        num_runs = int(sys.argv[4])
    except ValueError:
        print("Error: All arguments must be numeric")
        sys.exit(1)
    
    # Run simulation for different simulation times
    with open('simulation_results.csv', 'w', newline='') as csvfile:
        fieldnames = ['simulation_time', 'run', 'customers_served', 'customers_not_served', 'average_wait_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for sim_time in range(10, 101, 10):  # 10, 20, 30, ..., 100
            for run in range(1, num_runs + 1):
                results = main(arrival_rate, service_rate, sim_time, max_queue_size)
                writer.writerow({
                    'simulation_time': sim_time,
                    'run': run,
                    'customers_served': results['num_customers_served'],
                    'customers_not_served': results['num_customers_not_served'],
                    'average_wait_time': results['average_wait_time']
                })
    
    print(f"Results saved to simulation_results.csv")