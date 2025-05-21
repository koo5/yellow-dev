#!/usr/bin/env python3
"""
Script to generate customized docker-compose files and Dockerfiles.
Usage:
    python3 generate_compose.py --hollow=true|false --host-network=true|false
"""

import argparse
import copy
import json
import os
import sys
import yaml
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate customized docker-compose file')
    parser.add_argument('--hollow', type=str, choices=['true', 'false'], default='true',
                        help='Use hollow mode (bind-mount app sources) or full mode (default: true)')
    parser.add_argument('--host-network', type=str, choices=['true', 'false'], default='false',
                        help='Use host network mode (default: false)')
    return parser.parse_args()

def get_project_root():
    """Get the project root directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)

def load_docker_compose_template(project_root):
    """Load the docker-compose.template.yml file."""
    template_path = os.path.join(project_root, 'docker-compose.template.yml')
    with open(template_path, 'r') as f:
        return yaml.safe_load(f)

def prepare_output_dir(project_root):
    """Create the generated_compose_files directory if it doesn't exist."""
    output_dir = os.path.join(project_root, 'generated_compose_files')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def generate_hollow_dockerfile(project_root, context_path):
    """Generate a Dockerfile_hollow from Dockerfile_template."""
    template_path = os.path.join(project_root, context_path, 'Dockerfile_template')
    if not os.path.exists(template_path):
        print(f"Warning: {template_path} does not exist, skipping")
        return False
    
    # Read the template file
    with open(template_path, 'r') as src:
        content = src.read()
    
    # Generate Dockerfile_hollow
    hollow_path = os.path.join(project_root, context_path, 'Dockerfile_hollow')
    with open(hollow_path, 'w') as dst:
        dst.write(content)
    
    print(f"Generated {hollow_path}")
    return True

def generate_full_dockerfile(project_root, context_path):
    """Generate a Dockerfile_full from Dockerfile_template and Dockerfile_fragment_copy."""
    template_path = os.path.join(project_root, context_path, 'Dockerfile_template')
    fragment_path = os.path.join(project_root, context_path, 'Dockerfile_fragment_copy')
    
    if not os.path.exists(template_path):
        print(f"Warning: {template_path} does not exist, skipping")
        return False
    
    if not os.path.exists(fragment_path):
        print(f"Warning: {fragment_path} does not exist, skipping")
        return False
    
    # Read the template and fragment
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    with open(fragment_path, 'r') as f:
        fragment_content = f.read()
    
    # Generate Dockerfile_full by inserting fragment before CMD
    lines = template_content.splitlines()
    
    # Find the last non-empty line that doesn't start with CMD
    insert_point = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() and not lines[i].strip().startswith('CMD'):
            insert_point = i + 1
            break
    
    # Insert the copy fragment at the insert point
    lines.insert(insert_point, "\n# BEGIN COPY FRAGMENT")
    lines.insert(insert_point + 1, fragment_content)
    lines.insert(insert_point + 2, "# END COPY FRAGMENT\n")
    
    # Write to Dockerfile_full
    full_path = os.path.join(project_root, context_path, 'Dockerfile_full')
    with open(full_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Generated {full_path}")
    return True

def process_service_dockerfiles(compose_data, project_root, hollow):
    """Generate appropriate Dockerfiles for all services."""
    print(f"Generating {'hollow' if hollow else 'full'} Dockerfiles for all services...")
    
    for service_name, service_config in compose_data.get('services', {}).items():
        # Skip services that don't need modification
        if service_name in ['mariadb', 'mariadb-init', 'server-init']:
            continue
            
        # Generate Dockerfile for this service if it has a build section
        if 'build' in service_config:
            context = service_config['build'] if isinstance(service_config['build'], str) else service_config['build'].get('context', '.')
            
            if hollow:
                generate_hollow_dockerfile(project_root, context)
            else:
                generate_full_dockerfile(project_root, context)
            
            # Update the build configuration to use the appropriate Dockerfile
            if isinstance(service_config['build'], str):
                service_config['build'] = {
                    'context': service_config['build'],
                    'dockerfile': f"Dockerfile_{'hollow' if hollow else 'full'}"
                }
            else:
                service_config['build']['dockerfile'] = f"Dockerfile_{'hollow' if hollow else 'full'}"

def apply_host_network(compose_data, project_root, output_dir):
    """Apply host network mode to the compose file."""
    print("Applying host network mode...")
    
    # Create modified settings files for host network
    server_settings_path = os.path.join(project_root, 'yellow-server-settings.json')
    with open(server_settings_path, 'r') as f:
        server_settings = json.load(f)
    
    # Set database host to localhost
    server_settings['database']['host'] = '127.0.0.1'
    server_settings_modified_path = os.path.join(output_dir, 'yellow-server-settings.json')
    with open(server_settings_modified_path, 'w') as f:
        json.dump(server_settings, f, indent=2)
    
    # Messages settings
    messages_settings_path = os.path.join(project_root, 'yellow-server-module-messages-settings.json')
    with open(messages_settings_path, 'r') as f:
        messages_settings = json.load(f)
    
    # Set database host to localhost
    messages_settings['database']['host'] = '127.0.0.1'
    messages_settings_modified_path = os.path.join(output_dir, 'yellow-server-module-messages-settings.json')
    with open(messages_settings_modified_path, 'w') as f:
        json.dump(messages_settings, f, indent=2)
    
    # Remove networks section
    if 'networks' in compose_data:
        del compose_data['networks']
    
    # Set network_mode to host for each service
    for service_name, service_config in compose_data.get('services', {}).items():
        service_config['network_mode'] = 'host'
        if 'networks' in service_config:
            del service_config['networks']
        
        # Update environment variables
        if 'environment' not in service_config:
            service_config['environment'] = {}
        elif isinstance(service_config['environment'], list):
            env_dict = {}
            for item in service_config['environment']:
                if isinstance(item, str) and '=' in item:
                    key, value = item.split('=', 1)
                    env_dict[key] = value
            service_config['environment'] = env_dict
        
        # Set host-specific env vars
        if service_name in ['server', 'messages']:
            service_config['environment']['MARIA_HOST'] = '127.0.0.1'
            service_config['environment']['MESSAGES_HOST'] = 'localhost'
    
    # Update settings paths in volumes
    for service_name in ['server', 'messages']:
        if service_name in compose_data.get('services', {}):
            volumes = compose_data['services'][service_name].get('volumes', [])
            for i, volume in enumerate(volumes):
                if isinstance(volume, str):
                    if 'yellow-server-settings.json' in volume:
                        volumes[i] = f"{server_settings_modified_path}:/app/settings.json"
                    elif 'yellow-server-module-messages-settings.json' in volume:
                        volumes[i] = f"{messages_settings_modified_path}:/app/settings.json"

def apply_stack_network(compose_data):
    """Apply stack network mode (default) to the compose file."""
    print("Applying stack network mode...")
    
    # Ensure networks section exists
    if 'networks' not in compose_data:
        compose_data['networks'] = {
            'stack-network': {
                'driver': 'bridge'
            }
        }
    
    # Set environment variables for each service
    for service_name, service_config in compose_data.get('services', {}).items():
        # Update environment variables
        if 'environment' not in service_config:
            service_config['environment'] = {}
        elif isinstance(service_config['environment'], list):
            env_dict = {}
            for item in service_config['environment']:
                if isinstance(item, str) and '=' in item:
                    key, value = item.split('=', 1)
                    env_dict[key] = value
            service_config['environment'] = env_dict
        
        # Set network-specific env vars
        if service_name in ['server', 'messages']:
            service_config['environment']['MARIA_HOST'] = 'mariadb'
            service_config['environment']['MESSAGES_HOST'] = 'messages'
        
        # Ensure networks section exists for the service
        if 'networks' not in service_config and service_name not in ['mariadb-init', 'server-init']:
            service_config['networks'] = ['stack-network']

def apply_hollow_mode(compose_data):
    """Apply hollow mode: keep bind mounts for source code."""
    print("Applying hollow mode: keeping bind mounts...")
    
    # Set HOLLOW environment variable for all services
    for service_name, service_config in compose_data.get('services', {}).items():
        if 'environment' not in service_config:
            service_config['environment'] = {}
        
        service_config['environment']['HOLLOW'] = 'true'

def apply_full_mode(compose_data):
    """Apply full mode: remove bind mounts for source code and the common-init service."""
    print("Applying full mode: removing bind mounts and common-init service...")
    
    # Set HOLLOW environment variable for all services
    for service_name, service_config in compose_data.get('services', {}).items():
        if 'environment' not in service_config:
            service_config['environment'] = {}
        
        service_config['environment']['HOLLOW'] = 'false'
    
    # Remove app source bind mounts
    for service_name, service_config in compose_data.get('services', {}).items():
        # Skip services that don't need modification
        if service_name in ['mariadb', 'mariadb-init', 'server-init']:
            continue
        
        # Remove volume bind mounts that are for app sources, but keep settings.json files
        if 'volumes' in service_config:
            volumes_to_keep = []
            for volume in service_config['volumes']:
                # Keep settings.json files and non-app-source volumes
                if not (isinstance(volume, str) and './yellow-' in volume) or (isinstance(volume, str) and 'settings.json' in volume):
                    volumes_to_keep.append(volume)
                    # If keeping a settings.json file, log it
                    if isinstance(volume, str) and 'settings.json' in volume:
                        print(f"Preserving settings file mount {volume} for service {service_name}")
                else:
                    print(f"Removing bind mount {volume} from service {service_name}")
            
            # Replace volumes with filtered list
            service_config['volumes'] = volumes_to_keep
    
    # Remove the common-init service entirely
    if 'common-init' in compose_data.get('services', {}):
        print("Removing common-init service in full mode")
        del compose_data['services']['common-init']
        
    # Remove dependencies on common-init
    for service_name, service_config in compose_data.get('services', {}).items():
        if 'depends_on' in service_config and 'common-init' in service_config['depends_on']:
            print(f"Removing common-init dependency from service {service_name}")
            del service_config['depends_on']['common-init']
            
            # If depends_on is now empty, remove it
            if not service_config['depends_on']:
                del service_config['depends_on']
    
    # Add a Playwright container for testing in CI mode
    print("Adding Playwright container for testing...")
    
    # Create Playwright Dockerfile if it doesn't exist
    playwright_dir = os.path.join(get_project_root(), 'playwright-container')
    os.makedirs(playwright_dir, exist_ok=True)
    
    # Add the Playwright service to the compose file
    compose_data['services']['playwright'] = {
        'build': {
            'context': '.',
            'dockerfile': './playwright-container/Dockerfile',
            'args': {
                'USER_ID': "${USER_ID:-1000}",
                'GROUP_ID': "${GROUP_ID:-1000}"
            }
        },
        'environment': {
            'CI': 'true'
        },
        'network_mode': 'service:client',  # Share network with client container
        'volumes': [
            './test-results:/app/yellow-client/test-results',
            './playwright-report:/app/yellow-client/playwright-report'
        ],
        'depends_on': {
            'client': {'condition': 'service_healthy'}
        }
    }
    
    return compose_data

def main():
    """Main function to generate customized docker-compose files."""
    args = parse_args()
    project_root = get_project_root()
    
    hollow_mode = args.hollow.lower() == 'true'
    host_network = args.host_network.lower() == 'true'
    
    print(f"Generating customized docker-compose file...")
    print(f"Hollow mode: {hollow_mode}")
    print(f"Host network: {host_network}")
    
    # Prepare output directory
    output_dir = prepare_output_dir(project_root)
    
    # Load docker-compose template
    compose_data = load_docker_compose_template(project_root)
    
    # Make a deep copy to avoid modifying the original data
    modified_compose = copy.deepcopy(compose_data)
    
    # Process Dockerfiles for all services
    process_service_dockerfiles(modified_compose, project_root, hollow_mode)
    
    # Apply network mode
    if host_network:
        apply_host_network(modified_compose, project_root, output_dir)
        network_suffix = "hostnet"
    else:
        apply_stack_network(modified_compose)
        network_suffix = "stack"
    
    # Apply hollow/full mode
    if hollow_mode:
        apply_hollow_mode(modified_compose)
        mode_suffix = "hollow"
    else:
        apply_full_mode(modified_compose)
        mode_suffix = "full"
    
    # Generate the output filename
    output_filename = f"docker-compose.{mode_suffix}.{network_suffix}.yml"
    output_path = os.path.join(project_root, output_filename)
    
    # Write the modified compose file
    with open(output_path, 'w') as f:
        yaml.dump(modified_compose, f, default_flow_style=False)
    
    print(f"Generated customized docker-compose file: {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())