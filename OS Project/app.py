from flask import Flask, request, jsonify, render_template
from collections import deque

app = Flask(__name__)

class Process:
    def __init__(self, pid, burst_time, arrival_time=0, priority=0):
        self.pid = pid
        self.burst_time = burst_time
        self.arrival_time = arrival_time
        self.priority = priority
        self.remaining_time = burst_time
        self.completion_time = 0
        self.waiting_time = 0
        self.turnaround_time = 0
        self.start_time = 0  # To track the start time for Gantt chart

    def to_dict(self):
        return {
            "pid": self.pid,
            "burst_time": self.burst_time,
            "arrival_time": self.arrival_time,
            "priority": self.priority,
            "remaining_time": self.remaining_time,
            "completion_time": self.completion_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "start_time": self.start_time
        }

class Scheduler:
    def __init__(self, processes):
        self.processes = processes
        # self.processes_dict = {p.pid: p for p in self.processes}

    def fcfs(self):
        current_time = 0
        for process in sorted(self.processes, key=lambda x: x.arrival_time):
            if current_time < process.arrival_time:
                current_time = process.arrival_time
            process.waiting_time = current_time - process.arrival_time
            process.completion_time = current_time + process.burst_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.start_time = current_time
            current_time += process.burst_time

        return [process.to_dict() for process in self.processes]

    def sjf(self, preemptive=False):
        current_time = 0
        completed_processes = []
        if preemptive:
            process_queue = deque(sorted(self.processes, key=lambda x: x.arrival_time))
            while len(completed_processes) < len(self.processes):
                available_processes = [p for p in process_queue if p.arrival_time <= current_time and p not in completed_processes]
                if available_processes:
                    shortest_job = min(available_processes, key=lambda x: x.remaining_time)
                    if shortest_job.remaining_time == shortest_job.burst_time:
                        shortest_job.start_time = current_time
                    time_slice = min(shortest_job.remaining_time, 1)
                    current_time += time_slice
                    shortest_job.remaining_time -= time_slice
                    if shortest_job.remaining_time == 0:
                        shortest_job.completion_time = current_time
                        shortest_job.turnaround_time = current_time - shortest_job.arrival_time
                        shortest_job.waiting_time = shortest_job.turnaround_time - shortest_job.burst_time
                        completed_processes.append(shortest_job)
                else:
                    current_time += 1
        else:
            while len(completed_processes) < len(self.processes):
                available_processes = [p for p in self.processes if p.arrival_time <= current_time and p not in completed_processes]
                if available_processes:
                    shortest_job = min(available_processes, key=lambda x: x.burst_time)
                    if shortest_job.burst_time == shortest_job.remaining_time:
                        shortest_job.start_time = current_time
                    current_time += shortest_job.burst_time
                    shortest_job.completion_time = current_time
                    shortest_job.turnaround_time = current_time - shortest_job.arrival_time
                    shortest_job.waiting_time = shortest_job.turnaround_time - shortest_job.burst_time
                    completed_processes.append(shortest_job)
                else:
                    current_time += 1

        return [process.to_dict() for process in self.processes]

    from collections import deque

   

    def round_robin(self, quantum):
        current_time = 0
        queue = deque()
        processed_pids = set()

        # Initialize the queue with processes that have arrived by time 0
        for p in self.processes:
            if p.arrival_time <= current_time:
                queue.append(p)
                processed_pids.add(p.pid)

        while queue:
            process = queue.popleft()

            # If the process has not started yet, set its start time
            if process.start_time == 0:
                process.start_time = current_time

            # Process execution
            if process.remaining_time > quantum:
                process.remaining_time -= quantum
                current_time += quantum
                # Add new processes that have arrived while the current process was running
                for p in self.processes:
                    if p.arrival_time <= current_time and p.pid not in processed_pids:
                        queue.append(p)
                        processed_pids.add(p.pid)
                # Re-add the incomplete process to the queue
                queue.append(process)
            else:
                current_time += process.remaining_time
                process.remaining_time = 0
                process.completion_time = current_time
                process.turnaround_time = current_time - process.arrival_time
                process.waiting_time = process.turnaround_time - process.burst_time

                # Add new processes that have arrived while the current process was running
                for p in self.processes:
                    if p.arrival_time <= current_time and p.pid not in processed_pids:
                        queue.append(p)
                        processed_pids.add(p.pid)

            # Debug prints
            print(f"Current Time: {current_time}")
            print(f"Queue: {[p.pid for p in queue]}")
            print(f"Processing: {process.pid}")
            print(f"Process Start Time: {process.start_time}, Completion Time: {process.completion_time}, Turnaround Time: {process.turnaround_time}, Waiting Time: {process.waiting_time}")

        return [process.to_dict() for process in self.processes]



    def priority(self, preemptive=False):
        current_time = 0
        completed_processes = []
        process_queue = deque()
        processes = sorted(self.processes, key=lambda x: x.arrival_time)
        process_index = 0

        while len(completed_processes) < len(self.processes):
            # Add processes that have arrived to the queue
            while process_index < len(processes) and processes[process_index].arrival_time <= current_time:
                process_queue.append(processes[process_index])
                process_index += 1

            if process_queue:
                if preemptive:
                    available_processes = [p for p in process_queue if p.remaining_time > 0]
                    if available_processes:
                        highest_priority = max(available_processes, key=lambda x: x.priority)
                        if highest_priority.remaining_time == highest_priority.burst_time:
                            highest_priority.start_time = current_time
                        # Execute for one time unit
                        highest_priority.remaining_time -= 1
                        current_time += 1

                        if highest_priority.remaining_time == 0:
                            highest_priority.completion_time = current_time
                            highest_priority.turnaround_time = current_time - highest_priority.arrival_time
                            highest_priority.waiting_time = highest_priority.turnaround_time - highest_priority.burst_time
                            completed_processes.append(highest_priority)
                            process_queue.remove(highest_priority)
                    else:
                        current_time += 1
                else:
                    available_processes = [p for p in self.processes if p.arrival_time <= current_time and p not in completed_processes]
                    if available_processes:
                        highest_priority = max(available_processes, key=lambda x: x.priority)
                        if highest_priority.burst_time == highest_priority.remaining_time:
                            highest_priority.start_time = current_time
                        current_time += highest_priority.burst_time
                        highest_priority.completion_time = current_time
                        highest_priority.turnaround_time = current_time - highest_priority.arrival_time
                        highest_priority.waiting_time = highest_priority.turnaround_time - highest_priority.burst_time
                        completed_processes.append(highest_priority)
            else:
                current_time += 1

        return [process.to_dict() for process in self.processes]



@app.route("/")
def home():
    return render_template('index.html')

@app.route('/fcfs')
def fcfs_page():
    return render_template('fcfs.html')

@app.route('/sjf')
def sjf_page():
    return render_template('sjf.html')

@app.route('/rr')
def rr_page():
    return render_template('rr.html')

@app.route('/priority')
def priority_page():
    return render_template('priority.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    processes = [Process(p['pid'], p['burst_time'], p['arrival_time'], p.get('priority', 0)) for p in data['processes']]
    scheduler = Scheduler(processes)
    algorithm = data['algorithm']
    preemption = data.get('preemption', 'Non-Preemptive') == 'Preemptive'
    quantum = data.get('quantum', 3)

    if algorithm == "FCFS":
        result = scheduler.fcfs()
    elif algorithm == "SJF":
        result = scheduler.sjf(preemptive=preemption)
    elif algorithm == "RR":
        result = scheduler.round_robin(quantum)
    elif algorithm == "Priority":
        result = scheduler.priority(preemptive=preemption)
    else:
        return jsonify({"error": "Invalid algorithm selected"}), 400

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
