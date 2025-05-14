#!/usr/bin/env python3
import shlex
import subprocess
import time
import sys
import requests
from urllib.error import URLError
import os
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_command(cmd, cwd=None, capture_output=True):
    logger.info(f"Running command: {' '.join(cmd)}")
    
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
                logger.info(output.strip())
    else:
        # Run without capturing output - this will stream output directly to console
        logger.info(f"Running command with direct output: {' '.join(cmd)}")
        process = subprocess.run(cmd, cwd=cwd, check=False)
    
    return_code = process.returncode if not capture_output else process.poll()
    logger.info(f"Command finished with exit code: {return_code}")
    return return_code

def wait_for_service(url, max_attempts=300, delay=2):
    logger.info(f"Waiting for service at {url} (max_attempts={max_attempts}, delay={delay}s)...")
    attempts = 0
    while attempts < max_attempts:
        try:
            response = requests.get(url, timeout=5) # Added timeout for requests.get
            if response.status_code == 200:
                logger.info(f"Service at {url} is up and running!")
                return True
        except requests.exceptions.ConnectionError:
            logger.debug(f"ConnectionError on attempt {attempts + 1} for {url}.")
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout on attempt {attempts + 1} for {url}.")
        except Exception as e: # Catch other potential exceptions
            logger.warning(f"Unexpected error connecting to {url} on attempt {attempts + 1}: {e}")
            
        attempts += 1
        logger.info(f"Attempt {attempts}/{max_attempts} - Service not available yet, waiting {delay} seconds...")
        time.sleep(delay)
    
    logger.error(f"Service at {url} did not become available after {max_attempts} attempts.")
    return False

def wait_for_container_healthy(container_name, max_attempts=60, delay=5):
    logger.info(f"Waiting for container '{container_name}' to be healthy (max_attempts={max_attempts}, delay={delay}s)...")
    attempts = 0
    while attempts < max_attempts:
        try:
            cmd = ["docker", "inspect", f"--format='{{{{.State.Health.Status}}}}'", container_name]
            # Log the command being run
            logger.debug(f"Running health check command: {' '.join(cmd)}")
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False 
            )
            
            status = process.stdout.strip().replace("'", "") 
            
            if process.returncode == 0:
                logger.debug(f"Container '{container_name}' health check attempt {attempts + 1}: status is '{status}'")
                if status == "healthy":
                    logger.info(f"Container '{container_name}' is healthy.")
                    return True
                elif status == "unhealthy":
                    logger.error(f"Container '{container_name}' reported as unhealthy.")
                    return False 
            else:
                # This case can happen if the container doesn't exist (yet) or docker command fails
                logger.debug(f"Failed to get health status for container '{container_name}' on attempt {attempts + 1}. Docker inspect stderr: {process.stderr.strip()}")

        except Exception as e:
            logger.warning(f"Exception while checking health of container '{container_name}' on attempt {attempts + 1}: {e}")
            
        attempts += 1
        logger.info(f"Attempt {attempts}/{max_attempts} - Container '{container_name}' not healthy yet, waiting {delay} seconds...")
        time.sleep(delay)
        
    logger.error(f"Container '{container_name}' did not become healthy after {max_attempts} attempts.")
    return False

def run_docker_compose(project_root, stop_event):
    logger.info("Starting Docker Compose...")
    logger.debug(f"Project root for Docker Compose: {project_root}")
    
    # Get UID and GID
    uid = str(os.getuid())
    gid = str(os.getgid())
    logger.info(f"Setting UID={uid} and GID={gid} for Docker Compose.")
    
    # Prepare environment for Docker Compose
    compose_env = os.environ.copy()
    compose_env["UID"] = uid
    compose_env["GID"] = gid
    compose_env["CI"] = "true"
    
    cmd = ["docker", "compose", "up", "--build", "--remove-orphans"]
    logger.info(f"Running Docker Compose command: {shlex.join(cmd)} with UID={uid} GID={gid}")
    
    process = subprocess.Popen(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=compose_env
    )
    
    # Log Docker Compose output
    if process.stdout:
        for line in iter(process.stdout.readline, ''):
            logger.info(f"[Docker Compose] {line.strip()}")
            if stop_event.is_set(): # Check if stop event is set while reading output
                break
            if process.poll() is not None: # Check if process terminated while reading
                break
    
    # Wait for the stop event or process termination
    while not stop_event.is_set() and process.poll() is None:
        time.sleep(0.1) # Reduced sleep time for faster response
    
    if not stop_event.is_set() and process.poll() is not None:
        logger.error(f"Docker Compose exited unexpectedly with code {process.poll()}.")
        # Consider if sys.exit(1) is appropriate here or should be handled by main
        # For now, just log, main will handle overall script exit.
    
    # If we reach here because of stop_event or process ended, ensure termination
    if process.poll() is None: # If process is still running
        logger.info("Shutting down Docker Compose process...")
        process.terminate()
        try:
            process.wait(timeout=30)
            logger.info("Docker Compose process terminated.")
        except subprocess.TimeoutExpired:
            logger.warning("Docker Compose process did not terminate in time, killing.")
            process.kill()
            logger.info("Docker Compose process killed.")
    else:
        logger.info(f"Docker Compose process already exited with code {process.poll()}.")


def main():

    logger.info("Starting test execution script.")
    # Get the root directory of the project
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    project_root = os.path.dirname(script_dir)
    logger.info(f"Project root directory: {project_root}")
    
    # Initialize state variables
    test_status = 1  # Default to failure
    output_log = []  # Initialize log for Playwright output
    docker_thread = None
    stop_event = None
    failure_reason = "Unknown error"
    test_phase = "initialization"  # Track which phase we're in
    html_report_dir = None # Initialize html_report_dir
    
    try:
        logger.info("Creating stop event for Docker Compose thread.")
        stop_event = threading.Event()
        
        test_phase = "docker_startup"
        logger.info(f"Entering phase: {test_phase}")
        docker_thread = threading.Thread(
            target=run_docker_compose,
            args=(project_root, stop_event)
        )
        docker_thread.start()
        logger.info("Docker Compose thread started.")
        
        # Wait for the service to be available
        service_url = "http://localhost:3000" # Define service URL
        service_ready = wait_for_service(service_url)
        
        if not service_ready:
            failure_reason = f"Service at {service_url} did not start properly after multiple attempts"
            logger.error(failure_reason)
            raise Exception(failure_reason)

        # Wait for MariaDB container to be healthy.
        # The container_name is 'mariadb' as defined in docker-compose.yml
        mariadb_container_name = "mariadb"
        logger.info(f"Waiting for MariaDB container ('{mariadb_container_name}') to be healthy...")
        mariadb_healthy = wait_for_container_healthy(mariadb_container_name)
        
        if not mariadb_healthy:
            failure_reason = f"MariaDB container ('{mariadb_container_name}') did not become healthy."
            logger.error(failure_reason)
            raise Exception(failure_reason)
            
        test_phase = "database_setup" 
        logger.info(f"Entering phase: {test_phase}")
        logger.info("========== SETTING UP DATABASE ==========")
        db_setup_command = ["fish", "./scripts/ci_db.sh"]
        db_setup_result = run_command(db_setup_command, cwd=project_root)
        
        if db_setup_result != 0:
            failure_reason = f"Database setup failed with exit code: {db_setup_result} for command: {' '.join(db_setup_command)}"
            logger.error(failure_reason)
            raise Exception(failure_reason)
        logger.info("Database setup completed successfully.")
        
        # Define paths
        client_dir = os.path.join(project_root, "yellow-client")
        html_report_dir = os.path.join(client_dir, "playwright-report") # Assign here
        
        test_phase = "test_execution"
        logger.info(f"Entering phase: {test_phase}")
        
        logger.info("========== RUNNING PLAYWRIGHT TESTS ==========")
        playwright_test_command = [
            "npx", "playwright", "test", 
            "src/modules/org.libersoft.messages/tests/e2e/everything.test.ts",
            "--reporter=line"
        ]
        logger.info(f"Executing Playwright tests with command: {' '.join(playwright_test_command)}")
        
        process = subprocess.Popen(
            playwright_test_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=client_dir
        )
        
        logger.info("--- Playwright Test Output START ---")
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                stripped_line = line.strip()
                logger.info(stripped_line) # Log each line of test output
                output_log.append(stripped_line) # Append to output_log
        process.wait()
        logger.info("--- Playwright Test Output END ---")
        
        test_status = process.returncode
        logger.info(f"Playwright tests finished with exit code: {test_status}")
        
        if test_status == 0:
            failure_reason = None # Clear failure reason if tests passed
        else:
            failure_reason = f"Playwright tests failed with exit code: {test_status}"

    except Exception as e:
        logger.error(f"Error during {test_phase}: {e}", exc_info=True) # Log traceback
        test_status = 1
        if failure_reason == "Unknown error": # Update failure_reason if not already set by a specific check
            failure_reason = str(e)
    
    finally:
        logger.info("========== CLEANUP ==========")
        
        if stop_event and docker_thread and docker_thread.is_alive():
            logger.info("Signaling Docker Compose thread to stop...")
            stop_event.set()
            docker_thread.join(timeout=60) # Increased timeout for docker thread join
            if docker_thread.is_alive():
                logger.warning("Docker Compose thread did not stop in time.")
            else:
                logger.info("Docker Compose thread stopped.")
        
        logger.info("Ensuring Docker Compose is down...")
        run_command(["docker", "compose", "down", "--remove-orphans"], cwd=project_root, capture_output=True) # Capture output for this too
        logger.info("Docker Compose down command executed.")
        
        logger.info("========== PLAYWRIGHT TEST OUTPUT REPLAY ==========")
        if output_log:
            logger.info("Replaying Playwright Test Output:")
            for line in output_log:
                # Print directly to stdout to avoid logger formatting for this replay
                print(line)
        else:
            logger.info("No Playwright test output was captured.")

        logger.info("========== PLAYWRIGHT TEST RESULTS ==========")
        if test_phase == "test_execution":
            result_str = "PASSED" if test_status == 0 else "FAILED"
            logger.info(f"Playwright tests {result_str} with exit code: {test_status}")
        elif not service_ready and test_phase == "docker_startup": # Check if service_ready is defined
             logger.error(f"Tests FAILED during {test_phase} phase. Service did not become available.")
        else:
            logger.error(f"Tests FAILED during {test_phase} phase.")
        
        if html_report_dir and os.path.exists(html_report_dir): # Check html_report_dir before accessing
            logger.info(f"Full HTML report available in: {html_report_dir}")
        elif test_phase == "test_execution": # Only warn if tests were supposed to run
            logger.warning(f"Playwright HTML report directory not found at: {html_report_dir}")

        logger.info("========== TEST EXECUTION SUMMARY ==========")
        if test_status == 0:
            logger.info("✅ TESTS PASSED")
        else:
            logger.error("❌ TESTS FAILED")
            if failure_reason:
                logger.error(f"Reason: {failure_reason}")
            else:
                logger.error("Reason: An unspecified error occurred.")
                    
        logger.info(f"Final exit code: {test_status}")
        logger.info("===========================================")
        
        sys.exit(test_status)

if __name__ == "__main__":
    # Basic configuration is now at the top level of the script
    main()
