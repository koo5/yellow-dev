#!/usr/bin/env python3
import subprocess
import time
import sys
import requests
from urllib.error import URLError
import os
import threading


def run_command(cmd, cwd=None, capture_output=True):
    print(f"Running: {' '.join(cmd)}")
    
    if capture_output:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
    else:
        # Run without capturing output - this will stream output directly to console
        process = subprocess.run(cmd, cwd=cwd, check=False)
    
    return process.returncode if not capture_output else process.poll()

def wait_for_service(url, max_attempts=30, delay=2):
    print(f"Waiting for service at {url}...")
    attempts = 0
    while attempts < max_attempts:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Service at {url} is up and running!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        
        attempts += 1
        print(f"Attempt {attempts}/{max_attempts} - Service not available yet, waiting {delay} seconds...")
        time.sleep(delay)
    
    print(f"Service did not become available after {max_attempts} attempts")
    return False

def run_docker_compose(project_root, stop_event):
    # Start docker compose in the foreground
    process = subprocess.Popen(
        ["docker", "compose", "up", "--build", "--remove-orphans"],
        cwd=project_root
    )
    
    # Wait for the stop event or process termination
    while not stop_event.is_set() and process.poll() is None:
        time.sleep(0.5)
    
    if not stop_event.is_set() and process.poll() is not None:
        print("Docker Compose exited unexpectedly")
        sys.exit(1)
    
    # If we reach here because of stop_event, terminate the process
    if process.poll() is None:
        print("Shutting down Docker Compose...")
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()

def main():
    # Get the root directory of the project
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    test_result = 1  # Default to failure
    
    try:
        # Create an event to signal when to stop Docker Compose
        stop_event = threading.Event()
        
        # Start Docker Compose in a separate thread
        docker_thread = threading.Thread(
            target=run_docker_compose,
            args=(project_root, stop_event)
        )
        docker_thread.start()
        
        # Wait for the service to be available
        service_ready = wait_for_service("http://localhost:3000")
        
        if not service_ready:
            print("Service did not start properly")
            sys.exit(1)
            
        # Now that Docker is up, set up the database
        print("\n========== SETTING UP DATABASE ==========")
        db_setup_result = run_command(["fish", "./scripts/ci_db.sh"], cwd=project_root)
        
        if db_setup_result != 0:
            print("Database setup failed")
            sys.exit(1)
        
        # Define paths
        client_dir = os.path.join(project_root, "yellow-client")
        
        # Set up to capture detailed output
        output_log = []
        
        # Run playwright tests and capture output
        process = subprocess.Popen(
            [
                "npx", "playwright", "test", 
                "src/modules/org.libersoft.messages/tests/e2e/everything.test.ts",
                "--reporter=line"  # Use line reporter for more detailed output
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=client_dir
        )
        
        # Stream output to console and save for later
        print("\n========== RUNNING PLAYWRIGHT TESTS ==========")
        for line in process.stdout:
            sys.stdout.write(line)
            output_log.append(line.strip())
        
        process.wait()
        test_result = process.returncode
        
        # Capture test result and file paths for report generation later
        test_status = test_result
        json_report_file = os.path.join(client_dir, "test-results", "playwright-report.json")
        html_report_dir = os.path.join(client_dir, "playwright-report")
        
    except Exception as e:
        print(f"Error during test execution: {e}")
        test_status = 1
    
    finally:
        print("\n========== CLEANUP ==========")
        print("Shutting down Docker Compose...")
        
        # If we started the Docker thread, shut it down
        if 'stop_event' in locals() and 'docker_thread' in locals():
            stop_event.set()
            docker_thread.join(timeout=10)
        
        # Make absolutely sure docker compose is down, even if there was an error
        run_command(["docker", "compose", "down"], cwd=project_root)
        
        # Now print the test results after Docker is down
        print("\n========== PLAYWRIGHT TEST RESULTS ==========")
        
        # Simply print the captured output
        print("\nTest Output:")
        for line in output_log:
            print(line)
        
        # Print overall result
        result_str = "PASSED" if test_status == 0 else "FAILED"
        print(f"\nPlaywright tests {result_str} with exit code: {test_status}")
        
        # Check for HTML report directory
        if 'html_report_dir' in locals() and os.path.exists(html_report_dir):
            print(f"Full HTML report available in: {html_report_dir}")
        
        # Final summary
        print("\n========== TEST EXECUTION SUMMARY ==========")
        if test_status == 0:
            print("✅ TESTS PASSED")
        else:
            print("❌ TESTS FAILED")
        print(f"Exit code: {test_status}")
        print("===========================================\n")
        
        # Exit with the status from the test run
        sys.exit(test_status)

if __name__ == "__main__":
    main()