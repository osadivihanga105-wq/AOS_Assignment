#/bin/bash


LOG_FILE="system_monitor_log.txt"
ARCHIVE_DIR="ArchiveLogs"


log_action() {
    local action="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ACTION: $action" >> "$LOG_FILE"
}

monitor_processes() {
    echo "=========================================="
    echo "   CURRENT CPU AND MEMORY USAGE"
    echo "=========================================="
  
    top -bn1 | head -n 5
    
    echo -e "\nTop 10 Memory Consuming Processes:"
    echo "--------------------------------------------------"
   
    printf "%-10s %-10s %-10s %-10s %-20s\n" "PID" "USER" "%CPU" "%MEM" "COMMAND"
    ps aux --sort=-%mem | awk 'NR>1 {print $2, $1, $3, $4, $11}' | head -n 10 | column -t
    echo "--------------------------------------------------"
}

terminate_process() {
    read -p "Enter the PID of the process to terminate: " target_pid

    if [[ ! "$target_pid" =~ ^[0-9]+$ ]]; then
        echo "Error: Invalid PID format."
        return
    fi

    if [ "$target_pid" -lt 100 ]; then
        echo "ALERT: PID $target_pid is a critical system process. Termination denied."
        log_action "Blocked attempt to kill critical PID $target_pid"
        return
    fi

    read -p "Are you sure you want to terminate PID $target_pid? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        if kill -9 "$target_pid" 2>/dev/null; then
            echo "Process $target_pid successfully terminated."
            log_action "Terminated PID $target_pid"
        else
            echo "Error: Could not terminate PID $target_pid. (Process may not exist or permission denied)"
        fi
    else
        echo "Termination cancelled."
    fi
}

inspect_and_archive() {
    read -p "Enter the directory path to inspect: " dir_path
    
    if [ ! -d "$dir_path" ]; then
        echo "Error: Directory '$dir_path' does not exist."
        return
    fi

    echo "Disk Usage for $dir_path:"
    du -sh "$dir_path"

    if [ ! -d "$ARCHIVE_DIR" ]; then
        mkdir "$ARCHIVE_DIR"
        log_action "Created directory $ARCHIVE_DIR"
    fi

    echo "Searching for log files > 50MB..."
    found_logs=$(find "$dir_path" -type f -name "*.log" -size +50M)

    if [ -z "$found_logs" ]; then
        echo "No log files larger than 50MB were found."
    else
        for logfile in $found_logs; do
            timestamp=$(date +%Y%m%d_%H%M%S)
            filename=$(basename "$logfile")
            archive_name="${filename}_${timestamp}.tar.gz"
            
            echo "Compressing $filename..."
            tar -czf "$ARCHIVE_DIR/$archive_name" "$logfile" --remove-files
            log_action "Archived $filename to $ARCHIVE_DIR/$archive_name"
        done
        echo "Archiving complete."
    fi

    archive_size_kb=$(du -sk "$ARCHIVE_DIR" | cut -f1)
    if [ "$archive_size_kb" -gt 1048576 ]; then
        echo "!!! WARNING: $ARCHIVE_DIR exceeds 1GB (Current: $(du -sh $ARCHIVE_DIR | cut -f1)) !!!"
        log_action "WARNING: ArchiveLogs directory size exceeded 1GB"
    fi
}

while true; do
    echo -e "\n=========================================="
    echo "  UNIVERSITY DATA CENTRE MANAGER"
    echo "=========================================="
    echo "1) Monitor System & Top Processes"
    echo "2) Terminate a Process"
    echo "3) Inspect Disk & Archive Large Logs"
    echo "4) View Admin Audit Log"
    echo "5) Bye (Exit)"
    echo "=========================================="
    read -p "Please select an option [1-5]: " choice

    case $choice in
        1) monitor_processes ;;
        2) terminate_process ;;
        3) inspect_and_archive ;;
        4) 
            echo "--- System Monitor Log ---"
            [ -f "$LOG_FILE" ] && cat "$LOG_FILE" || echo "No logs found."
            ;;
        5) 
            read -p "Are you sure you want to exit? (Y/N): " exit_confirm
            if [[ "$exit_confirm" =~ ^[Yy]$ ]]; then
                log_action "System tool closed by user."
                echo "Goodbye!"
                exit 0
            fi
            ;;
        *) echo "Invalid selection. Please choose 1-5." ;;
    esac
done
