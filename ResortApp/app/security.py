import requests
import sys
import os

def verify_instance():
    # Only run check in production/Ubuntu
    if os.name == "nt":
        return
        
    try:
        response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/id",
            headers={"Metadata-Flavor": "Google"},
            timeout=5
        )
        if response.status_code == 200:
            instance_id = response.text.strip()
            # Hardcoded instance ID for 34.71.114.198
            allowed_id = "4726854500094706993"
            if instance_id != allowed_id:
                print(f"CRITICAL SECURITY ERROR: Unauthorized Environment ({instance_id})")
                sys.exit(1)
        else:
            print("CRITICAL SECURITY ERROR: Verification Required")
            sys.exit(1)
    except Exception as e:
        print(f"CRITICAL SECURITY ERROR: Environment Check Failed ({e})")
        sys.exit(1)

if __name__ == "__main__":
    verify_instance()
