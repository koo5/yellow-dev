#!/usr/bin/env python3
import docker
import time
import sys

def remove_volumes():
    """Remove yellow-dev Docker volumes with retry logic."""
    client = docker.from_env()
    volumes_to_remove = [
        'yellow-dev_mariadb',
        'yellow-dev_mariadb_tmp',
        'yellow-dev_server_logs',
        'yellow-dev_server_tmp'
    ]
    
    while True:
        failed_volumes = []
        
        for volume_name in volumes_to_remove:
            try:
                volume = client.volumes.get(volume_name)
                volume.remove(force=True)
                print(f"✓ Removed volume: {volume_name}")
            except docker.errors.NotFound:
                print(f"- Volume not found (already removed): {volume_name}")
            except docker.errors.APIError as e:
                print(f"✗ Failed to remove volume {volume_name}: {e}")
                failed_volumes.append(volume_name)
        
        if not failed_volumes:
            print("\nSuccessfully removed all volumes!")
            break
        else:
            print(f"\nFailed to remove {len(failed_volumes)} volume(s): {', '.join(failed_volumes)}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    try:
        remove_volumes()
    except docker.errors.DockerException as e:
        print(f"Docker error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)