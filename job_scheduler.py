#bin/bash

QUEUE_FILE="job_queue.txt"
COMPLETED_FILE="completed_jobs.txt"
LOG_FILE="scheduler_log.txt"

touch "$QUEUE_FILE" "$COMPLETED_FILE" "$LOG_FILE"

log_event() {
    local message=$1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" >> "$LOG_FILE"
}

view_pending() {
    if [ ! -s "$QUEUE_FILE" ]; then
        echo -e "\n[!] No pending jobs in the queue."
    else
        echo -e "\n--- Current Pending Jobs ---"
        printf "%-12s %-15s %-10s %-8s\n" "STUDENT ID" "JOB NAME" "TIME(s)" "PRIORITY"
        echo "------------------------------------------------------------"
        while IFS='|' read -r sid jname etime prio; do
            printf "%-12s %-15s %-10s %-8s\n" "$sid" "$jname" "$etime" "$prio"
        done < "$QUEUE_FILE"
    fi
}

submit_job() {
    echo -e "\n--- Submit New Job Request ---"
    read -p "Enter Student ID: " sid
    read -p "Enter Job Name: " job_name
    read -p "Enter Estimated Execution Time (seconds): " exec_time
    read -p "Enter Priority (1-10, where 10 is highest): " priority

    if [[ ! "$exec_time" =~ ^[0-9]+$ ]] || [[ ! "$priority" =~ ^[0-9]+$ ]]; then
        echo "Error: Execution time and Priority must be numbers."
        return
    fi

    echo "$sid|$job_name|$exec_time|$priority" >> "$QUEUE_FILE"
    
    log_event "SUBMISSION: Student $sid submitted '$job_name' (Prio: $priority, Time: ${exec_time}s)"
    echo "Job successfully added to queue."
}

process_priority() {
    if [ ! -s "$QUEUE_FILE" ]; then
        echo "Queue is empty. Nothing to process."
        return
    fi

    echo -e "\n--- Processing Jobs (Priority Scheduling: Highest First) ---"
    
    sort -t'|' -k4,4nr "$QUEUE_FILE" | while IFS='|' read -r sid jname etime prio; do
        echo ">> Executing Job: $jname (Priority: $prio) for $etime seconds..."
        sleep "$etime" # Simulate work
        
        echo "$sid|$jname|Priority|$etime|$(date)" >> "$COMPLETED_FILE"
        log_event "EXECUTION: Completed '$jname' (Student: $sid) via Priority"
    done

    > "$QUEUE_FILE" # Clear the queue after processing
    echo "All jobs in queue have been processed."
}

process_round_robin() {
    if [ ! -s "$QUEUE_FILE" ]; then
        echo "Queue is empty. Nothing to process."
        return
    fi

    local quantum=5
    echo -e "\n--- Processing Jobs (Round Robin: Time Quantum = 5s) ---"

    while [ -s "$QUEUE_FILE" ]; do
     
        IFS='|' read -r sid jname etime prio < "$QUEUE_FILE"
      
        sed -i '1d' "$QUEUE_FILE"

        if [ "$etime" -gt "$quantum" ]; then
            echo ">> $jname: Running 5s slice. Remaining: $((etime - quantum))s"
            sleep $quantum
    
            echo "$sid|$jname|$((etime - quantum))|$prio" >> "$QUEUE_FILE"
        else
            echo ">> $jname: Finishing remaining ${etime}s..."
            sleep "$etime"
            echo "$sid|$jname|RoundRobin|$etime|$(date)" >> "$COMPLETED_FILE"
            log_event "EXECUTION: Completed '$jname' (Student: $sid) via RR"
        fi
    done
    echo "Round Robin processing complete."
}

while true; do
    echo -e "\n=========================================="
    echo "   UNIVERSITY HPC JOB SCHEDULER"
    echo "=========================================="
    echo "1) View Pending Jobs"
    echo "2) Submit a Job Request"
    echo "3) Process Queue: Round Robin (5s)"
    echo "4) Process Queue: Priority Scheduling"
    echo "5) View Completed Jobs"
    echo "6) Bye (Exit)"
    echo "=========================================="
    read -p "Action [1-6]: " choice

    case $choice in
        1) view_pending ;;
        2) submit_job ;;
        3) process_round_robin ;;
        4) process_priority ;;
        5) 
            echo -e "\n--- Completed Jobs History ---"
            [ -s "$COMPLETED_FILE" ] && column -t -s'|' "$COMPLETED_FILE" || echo "No history found."
            ;;
        6) 
            read -p "Are you sure you want to exit? (y/n): " quit
            if [[ "$quit" =~ ^[Yy]$ ]]; then
                echo "Exiting Scheduler. Goodbye!"
                exit 0
            fi
            ;;
        *) echo "Invalid option. Please enter 1-6." ;;
    esac
done
