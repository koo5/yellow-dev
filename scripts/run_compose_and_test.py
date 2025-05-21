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
import yaml
import json
import shutil
import copy
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_command(cmd, cwd=None, capture_output=True, env=None):
    logger.info(f"Running command: {' '.join(cmd)}")
    
    if capture_output:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            env=env
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
        process = subprocess.run(cmd, cwd=cwd, check=False, env=env)
    
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
        logger.info(f"Attempt {attempts}/{max_attempts} - Service not available yet, retry in {delay} seconds...")
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

def generate_full_mode_compose_file(project_root, compose_data):
    """
    Modify the docker-compose file for full mode.
    In full mode, we remove volume bind mounts and handle package installation inside Dockerfile.
    We also update Dockerfile paths to use Dockerfile_full.
    """
    logger.info("Generating full mode compose file...")
    
    # Make a deep copy to avoid modifying the original data
    full_mode_compose = copy.deepcopy(compose_data)
    
    # For each service, modify as needed for full mode
    for service_name, service_config in full_mode_compose.get('services', {}).items():
        # Skip services that don't need modification
        if service_name in ['mariadb', 'mariadb-init']:
            continue
            
        # Remove volume bind mounts that are for app sources
        if 'volumes' in service_config:
            # Keep only non-app-source volumes (like logs, database, etc.)
            volumes_to_keep = []
            for volume in service_config['volumes']:
                # Check if it's an app source bind mount
                # App source bind mounts typically contain project root path
                if not (isinstance(volume, str) and './yellow-' in volume):
                    volumes_to_keep.append(volume)
                else:
                    logger.debug(f"Removing bind mount {volume} from service {service_name} for full mode")
            
            # Replace volumes with filtered list
            service_config['volumes'] = volumes_to_keep
        
        # Update build configuration to use Dockerfile_full if available
        if 'build' in service_config:
            # If it's a dictionary with context and dockerfile
            if isinstance(service_config['build'], dict):
                build_config = service_config['build']
                context = build_config.get('context', '.')
                
                # Check if Dockerfile_full exists in the context
                dockerfile_full_path = os.path.join(project_root, context, 'Dockerfile_full')
                if os.path.exists(dockerfile_full_path):
                    logger.info(f"Using Dockerfile_full for service {service_name}")
                    build_config['dockerfile'] = 'Dockerfile_full'
                    
                    # Add a stage name for the base image if not already specified
                    if 'target' not in build_config:
                        # Set the target to be the service name with a 'full' suffix
                        build_config['target'] = f"{service_name}_full"
                    
                    # Add args for hollow mode
                    if 'args' not in build_config:
                        build_config['args'] = {}
                    build_config['args']['HOLLOW'] = 'false'
                    
                    # Add dependency on base image
                    base_service_name = f"{service_name}-base"
                    if 'depends_on' not in service_config:
                        service_config['depends_on'] = {}
                    
                    service_config['depends_on'][base_service_name] = {'condition': 'service_completed_successfully'}
            
            # If it's just a string (context path)
            elif isinstance(service_config['build'], str):
                context = service_config['build']
                dockerfile_full_path = os.path.join(project_root, context, 'Dockerfile_full')
                
                if os.path.exists(dockerfile_full_path):
                    logger.info(f"Using Dockerfile_full for service {service_name}")
                    # Convert to use full mode with base image
                    service_config['build'] = {
                        'context': context,
                        'dockerfile': 'Dockerfile_full',
                        'args': {
                            'HOLLOW': 'false'
                        }
                    }
                    
                    # Add dependency on base image
                    base_service_name = f"{service_name}-base"
                    if 'depends_on' not in service_config:
                        service_config['depends_on'] = {}
                    
                    service_config['depends_on'][base_service_name] = {'condition': 'service_completed_successfully'}
    
    return full_mode_compose

def run_docker_compose(project_root, stop_event, host_network=False, hollow=False):
    logger.info("Starting Docker Compose...")
    logger.debug(f"Project root for Docker Compose: {project_root}")
    
    # Detect if we're running in CI
    is_ci = os.environ.get('CI', 'false').lower() == 'true'
    logger.info(f"Running in CI environment: {is_ci}")
    logger.info(f"Using host network: {host_network}")
    logger.info(f"Using hollow mode: {hollow}")
    
    uid = str(os.getuid())
    gid = str(os.getgid())
    logger.info(f"host UID={uid} and GID={gid}")
    
    # Prepare environment for Docker Compose
    compose_env = os.environ.copy()
    compose_env["UID"] = uid
    compose_env["GID"] = gid
    compose_env["CI"] = "true" if is_ci else "false"
    compose_env["HOLLOW"] = "true" if hollow else "false"
    
    # Set environment variables based on network mode
    compose_env["MARIA_HOST"] = "127.0.0.1" if host_network else "mariadb"
    compose_env["MESSAGES_HOST"] = "localhost" if host_network else "messages"
    logger.info(f"Setting MARIA_HOST={compose_env['MARIA_HOST']}")
    logger.info(f"Setting MESSAGES_HOST={compose_env['MESSAGES_HOST']}")
    logger.info(f"Setting HOLLOW={compose_env['HOLLOW']}")

    # Create the generated_compose_files directory if it doesn't exist
    generated_compose_dir = os.path.join(project_root, "generated_compose_files")
    Path(generated_compose_dir).mkdir(parents=True, exist_ok=True)
    
    # Load the original docker-compose.yml file
    compose_file_path = os.path.join(project_root, "docker-compose.yml")
    with open(compose_file_path, 'r') as f:
        compose_data = yaml.safe_load(f)
    
    # The path to the compose file that will be used
    final_compose_file = compose_file_path
    
    # If using host network, we need to modify the compose file and settings
    if host_network:
        logger.info("Creating modified settings files for host network mode")
        
        # Create server settings with localhost settings
        server_settings_path = os.path.join(project_root, "yellow-server-settings.json")
        with open(server_settings_path, 'r') as f:
            server_settings = json.load(f)
        
        # Ensure database host is set to 127.0.0.1
        server_settings['database']['host'] = "127.0.0.1"
        
        # Write modified settings file
        server_settings_modified_path = os.path.join(generated_compose_dir, "yellow-server-settings.json")
        with open(server_settings_modified_path, 'w') as f:
            json.dump(server_settings, f, indent=1)
        
        # Create messages module settings
        messages_settings_path = os.path.join(project_root, "yellow-server-module-messages-settings.json")
        with open(messages_settings_path, 'r') as f:
            messages_settings = json.load(f)
        
        # Ensure database host is set to 127.0.0.1
        messages_settings['database']['host'] = "127.0.0.1"
        
        # Write modified settings file
        messages_settings_modified_path = os.path.join(generated_compose_dir, "yellow-server-module-messages-settings.json")
        with open(messages_settings_modified_path, 'w') as f:
            json.dump(messages_settings, f, indent=1)
        
        # Create modified compose file with host network
        logger.info("Creating modified compose file with host network mode")
        final_compose_file = os.path.join(generated_compose_dir, "docker-compose-host-network.yml")
        
        # Make a deep copy to avoid modifying the original data
        host_network_compose = copy.deepcopy(compose_data)
        
        # Remove any network definitions
        if 'networks' in host_network_compose:
            del host_network_compose['networks']
        
        # Set network_mode to host for all services
        for service_name, service_config in host_network_compose.get('services', {}).items():
            service_config['network_mode'] = 'host'
            if 'networks' in service_config:
                del service_config['networks']
        
        # Update the settings file paths in the volumes
        for service_name in ['server', 'messages']:
            if service_name in host_network_compose.get('services', {}):
                volumes = host_network_compose['services'][service_name].get('volumes', [])
                for i, volume in enumerate(volumes):
                    if 'yellow-server-settings.json' in volume:
                        volumes[i] = f"{server_settings_modified_path}:/app/settings.json"
                    elif 'yellow-server-module-messages-settings.json' in volume:
                        volumes[i] = f"{messages_settings_modified_path}:/app/settings.json"
        
        # Update compose_data with the host network modifications
        compose_data = host_network_compose
        
        # Update the final compose file path
        final_compose_file = os.path.join(generated_compose_dir, "docker-compose-host-network.yml")
        
    # Handle full mode (non-hollow)
    if not hollow:
        # This is full mode - generate modified compose file with no bind mounts
        logger.info("Creating modified compose file for full (non-hollow) mode")
        full_mode_compose = generate_full_mode_compose_file(project_root, compose_data)
        compose_data = full_mode_compose
        
        if host_network:
            final_compose_file = os.path.join(generated_compose_dir, "docker-compose-host-network-full.yml")
        else:
            final_compose_file = os.path.join(generated_compose_dir, "docker-compose-full.yml")
    
    # Write the final compose file 
    if final_compose_file != compose_file_path:
        with open(final_compose_file, 'w') as f:
            yaml.dump(compose_data, f, default_flow_style=False)
        logger.info(f"Created modified compose file: {final_compose_file}")
    
    # Configure the docker-compose command
    cmd_base = ["docker", "compose"]
    
    # Add file path if needed
    if final_compose_file != compose_file_path:
        cmd_base.extend(["-f", final_compose_file])
    
    # In full mode, include the base-images profile
    if not hollow:
        cmd_base.extend(["--profile", "base-images"])
    
    # Complete the command
    if is_ci:
        cmd = cmd_base + ["up", "--build", "--remove-orphans"]
    else:
        cmd = cmd_base + ["up", "--build", "--remove-orphans"]
    
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


def main(host_network=False, hollow=False):
    logger.info("Starting test execution script.")
    # Get the root directory of the project
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    logger.info(f"Project root directory: {project_root}")
    
    # Detect if we're running in CI
    is_ci = os.environ.get('CI', 'false').lower() == 'true'
    # Check for HOLLOW env var
    hollow_env = os.environ.get('HOLLOW', 'false').lower() == 'true'
    # Use env var if provided, otherwise use the function parameter
    hollow = hollow_env if hollow_env else hollow
    logger.info(f"Running in CI environment: {is_ci}")
    logger.info(f"Using host network mode: {host_network}")
    logger.info(f"Using hollow mode: {hollow}")
    
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
            args=(project_root, stop_event, host_network, hollow)
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
        
        # Pass CI environment variable to database setup script
        db_setup_env = os.environ.copy()
        db_setup_env["CI"] = "true" if is_ci else "false"

        # Run db setup with CI env vars
        db_setup_result = run_command(db_setup_command, cwd=project_root, env=db_setup_env)
        
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
        
        # Check if we're using containerized Playwright
        use_playwright_container = is_ci
        
        if use_playwright_container:
            logger.info("Using Playwright container for tests")
            # Run tests using the Playwright container
            playwright_compose_file = os.path.join(project_root, "playwright-container/docker-compose.playwright.yml")
            
            # Run Playwright in Docker
            playwright_test_command = [
                "docker", "compose", 
                "-f", final_compose_file,
                "-f", playwright_compose_file,
                "run", "playwright"
            ]
            
            logger.info(f"Executing Playwright container with command: {' '.join(playwright_test_command)}")
            
            # Pass environment variables
            playwright_env = compose_env.copy()
        else:
            # Run tests locally
            playwright_test_command = [
                "npx", "playwright", "test", "--reporter=line,github"
            ]
            logger.info(f"Executing local Playwright tests with command: {' '.join(playwright_test_command)}")
            
            # Pass CI flag to the test environment
            playwright_env = os.environ.copy()
            playwright_env["CI"] = "true" if is_ci else "false"
            
        process = subprocess.Popen(
            playwright_test_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=client_dir if not use_playwright_container else project_root,
            env=playwright_env
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
        # Use the same CI-specific docker-compose command for shutdown
        generated_compose_dir = os.path.join(project_root, "generated_compose_files")
        compose_file = "docker-compose.yml"
        
        if host_network:
            # Use the host network compose file if it exists
            host_network_file = os.path.join(generated_compose_dir, "docker-compose-host-network.yml")
            if os.path.exists(host_network_file):
                compose_file = host_network_file
                logger.info(f"Using host network compose file for shutdown: {compose_file}")
        
        if is_ci:
            down_command = [
                "docker", "compose", 
                "-f", compose_file,
                "down", "--remove-orphans"
            ]
        else:
            if host_network and os.path.exists(os.path.join(generated_compose_dir, "docker-compose-host-network.yml")):
                down_command = ["docker", "compose", "-f", compose_file, "down", "--remove-orphans"]
            else:
                down_command = ["docker", "compose", "down", "--remove-orphans"]
            
        run_command(down_command, cwd=project_root, capture_output=True) # Capture output for this too
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Docker Compose and tests')
    parser.add_argument('--host-network', dest='host_network', action='store_true',
                        help='Use host network mode')
    parser.add_argument('--hollow', dest='hollow', action='store_true',
                        help='Use hollow mode (bind-mount app sources instead of copying them)')
    parser.set_defaults(host_network=False, hollow=False)
    
    args = parser.parse_args()
    main(host_network=args.host_network, hollow=args.hollow)