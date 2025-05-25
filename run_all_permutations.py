#!/usr/bin/env python3
"""
Run ci-run.sh in all 8 possible permutations of hollow, host-network, and http flags.
Clean between runs using clean.py.
Stop if any run fails.
"""

import subprocess
import sys
import time
from itertools import product

def run_command(cmd, description=None):
    """Run a command and return True if successful, False otherwise."""
    if description:
        print(f"\n{'='*80}")
        print(f"[PERMUTATION] {description}")
        print(f"[PERMUTATION] Running: {' '.join(cmd)}")
        print(f"{'='*80}\n")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    end_time = time.time()
    
    duration = end_time - start_time
    minutes = int(duration // 60)
    seconds = duration % 60
    
    if result.returncode == 0:
        if description:
            print(f"\n[PERMUTATION] ✅ SUCCESS - {description} (took {minutes}m {seconds:.1f}s)")
        return True
    else:
        print(f"\n[PERMUTATION] ❌ FAILED - {description} (took {minutes}m {seconds:.1f}s)")
        print(f"[PERMUTATION] Exit code: {result.returncode}")
        return False

def main():
    """Run all permutations of ci-run.sh."""
    # All possible permutations
    hollow_values = ['true', 'false']
    host_network_values = ['true', 'false']
    http_values = ['true', 'false']
    
    permutations = list(product(hollow_values, host_network_values, http_values))
    
    print(f"[PERMUTATION] Starting CI runs for all {len(permutations)} permutations...")
    print(f"[PERMUTATION] Permutations: hollow × host-network × http")
    
    successful_runs = 0
    failed_runs = 0
    
    overall_start = time.time()
    
    for i, (hollow, host_network, http) in enumerate(permutations, 1):
        # Create description
        mode = "hollow" if hollow == 'true' else "full"
        network = "hostnet" if host_network == 'true' else "stack"
        protocol = "http" if http == 'true' else "https"
        description = f"{mode}.{network}.{protocol} (permutation {i}/{len(permutations)})"

        clean_result = run_command(['python3', 'clean.py'])
        if not clean_result:
            print(f"[PERMUTATION] Clean failed, stopping.")
            failed_runs += 1
            break
        
        # Run ci-run.sh with the current permutation
        cmd = ['./ci-run.sh', hollow, host_network, http, 'true', 'true']
        success = run_command(cmd, description)
        
        if success:
            successful_runs += 1
        else:
            failed_runs += 1
            print(f"\n[PERMUTATION] Stopping due to failure in {description}")
            break
    
    # Final summary
    overall_end = time.time()
    total_duration = overall_end - overall_start
    total_minutes = int(total_duration // 60)
    total_seconds = total_duration % 60
    
    print(f"\n{'='*80}")
    print(f"[PERMUTATION] FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"[PERMUTATION] Total permutations attempted: {successful_runs + failed_runs}/{len(permutations)}")
    print(f"[PERMUTATION] Successful: {successful_runs}")
    print(f"[PERMUTATION] Failed: {failed_runs}")
    print(f"[PERMUTATION] Total time: {total_minutes}m {total_seconds:.1f}s")
    
    if failed_runs > 0:
        print(f"[PERMUTATION] ❌ CI runs failed")
        sys.exit(1)
    else:
        print(f"[PERMUTATION] ✅ All CI runs completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()