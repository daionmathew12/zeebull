
import os
import time

log_file = "c:\\releasing\\orchid\\ResortApp\\server_output.log"
error_itc = "DEBUG: Entered get_itc_register"
error_slab = "DEBUG: Entered get_room_tariff_slab_report"

found = False
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        # Read file line by line to avoid memory issues
        for line in f:
            if error_itc in line or error_slab in line:
                print(f"FOUND ERROR: {line.strip()}")
                found = True
                # Print next few lines if they are traceback
                try:
                    for _ in range(20):
                        next_line = next(f)
                        print(next_line.strip())
                        if not next_line.strip().startswith("Traceback") and not next_line.strip().startswith("File"):
                             pass # Continue printing to see the message
                except StopIteration:
                    break

if not found:
    print("No errors found in server_output.log matching the patterns.")
