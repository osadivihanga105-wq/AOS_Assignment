#/bin/bash

SUBMISSION_DIR="StudentSubmissions"
SUBMISSION_LOG="submission_log.txt"
LOGIN_LOG="login_log.txt"
ATTEMPT_COUNT_FILE=".login_attempts" 
LOCK_FILE=".account_locked"          

mkdir -p "$SUBMISSION_DIR"
touch "$SUBMISSION_LOG" "$LOGIN_LOG"

simulate_login() {
   
    if [ -f "$LOCK_FILE" ]; then
        echo -e "\n[!] ACCESS DENIED: Account is locked due to 3 failed attempts."
        echo "Contact the Administrator to reset."
        return
    fi

    read -p "Username: " username
    read -sp "Password: " password
    echo -e "\n"

    CORRECT_PASS="Exam2026"
    current_time=$(date +%s)

    if [ "$password" == "$CORRECT_PASS" ]; then
        echo "Login Successful! Welcome, $username."
        rm -f "$ATTEMPT_COUNT_FILE" # Reset attempts on success
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: User '$username' logged in." >> "$LOGIN_LOG"
    else
      
        prev_attempts=$(cat "$ATTEMPT_COUNT_FILE" 2>/dev/null || echo 0)
        new_count=$((prev_attempts + 1))
        echo "$new_count" > "$ATTEMPT_COUNT_FILE"

        echo "[$(date '+%Y-%m-%d %H:%M:%S')] FAILED: User '$username' incorrect password." >> "$LOGIN_LOG"

        last_mod=$(stat -c %Y "$ATTEMPT_COUNT_FILE" 2>/dev/null || echo 0)
        if [ "$((current_time - last_mod))" -lt 60 ] && [ "$prev_attempts" -gt 0 ]; then
            echo "WARNING: Rapid login attempts detected! (Suspicious Activity)"
        fi

        echo "Incorrect password. Attempt $new_count of 3."

        if [ "$new_count" -ge 3 ]; then
            touch "$LOCK_FILE"
            echo "SECURITY ALERT: 3 failed attempts reached. Account is now LOCKED."
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] LOCKOUT: User '$username' account locked." >> "$LOGIN_LOG"
        fi
    fi
}

submit_assignment() {
    read -p "Enter the full path of the file to submit: " file_path


    if [[ ! -f "$file_path" ]]; then
        echo "Error: File '$file_path' does not exist."
        return
    fi

    if [[ ! "$file_path" =~ \.(pdf|docx)$ ]]; then
        echo "Error: Invalid file format. Only .pdf and .docx are allowed."
        return
    fi

    file_size=$(stat -c%s "$file_path")
    if [ "$file_size" -gt 5242880 ]; then
        echo "Error: File size exceeds 5MB limit."
        return
    fi

    file_name=$(basename "$file_path")
    if [ -f "$SUBMISSION_DIR/$file_name" ]; then
        existing_hash=$(md5sum "$SUBMISSION_DIR/$file_name" | awk '{print $1}')
        new_hash=$(md5sum "$file_path" | awk '{print $1}')
        
        if [ "$existing_hash" == "$new_hash" ]; then
            echo "Error: A file with the same name and content has already been submitted."
            return
        fi
    fi

    cp "$file_path" "$SUBMISSION_DIR/"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUBMITTED: $file_name (Size: $file_size bytes)" >> "$SUBMISSION_LOG"
    echo "Success: '$file_name' submitted and logged."
}

while true; do
    echo -e "\n=========================================="
    echo "   SECURE EXAM SUBMISSION SYSTEM"
    echo "=========================================="
    echo "1) Submit an Assignment"
    echo "2) Check if File is Submitted"
    echo "3) List All Submitted Assignments"
    echo "4) Simulate Login Attempt"
    echo "5) Exit System"
    echo "=========================================="
    read -p "Select an option [1-5]: " choice

    case $choice in
        1) submit_assignment ;;
        2) 
            read -p "Enter filename to check: " check_name
            if [ -f "$SUBMISSION_DIR/$check_name" ]; then
                echo "Result: '$check_name' was found in the submission database."
            else
                echo "Result: No record of '$check_name'."
            fi
            ;;
        3) 
            echo "--- List of Submissions ---"
            ls -lh "$SUBMISSION_DIR" 
            ;;
        4) simulate_login ;;
        5) 
            read -p "Are you sure you want to exit? (y/n): " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                echo "Exiting system. Goodbye!"
                exit 0
            fi
            ;;
        *) echo "Invalid option. Please try again." ;;
    esac
done
