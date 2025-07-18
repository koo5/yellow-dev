import click
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_local(command, cwd=None):
	result = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True)
	if result.returncode != 0:
		print(f"[LOCAL ERROR] {command}\n{result.stderr}", file=sys.stderr)
		sys.exit(result.returncode)
	return result.stdout.strip()


def run_remote(ssh_host, command):
	full_cmd = f'ssh {ssh_host} "{command.replace(\'"\', r\'\\\"\')}"'
	result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
	output = result.stdout
	if result.returncode != 0:
		output += f"\n[ERROR on {ssh_host}]\n{result.stderr}"
	return ssh_host, output, result.returncode


@click.command()
@click.option('--ssh', multiple=True, required=True, help='SSH connection strings (user@host[:port])')
def main(ssh):
	# (1) Get current git head hash (in yellow-client)
	client_head = run_local("git -C yellow-client rev-parse HEAD")
	print(f"GIT HEAD of yellow-client: {client_head}")

	# (2) Push current HEAD to all remotes
	print("Running 'git push' ...")
	run_local("git push")

	# (3) Build remote command(s) to run with sharding
	total_shards = len(ssh)
	print(f"Running with {total_shards} shards")

	print("\n== Executing remote jobs in parallel ==\n")

	# (4) Run all SSH jobs in parallel with different shard parameters
	with ThreadPoolExecutor(max_workers=len(ssh)) as executor:
		jobs = {}
		for i, host in enumerate(ssh):
			shard_param = f"--shard={i+1}/{total_shards}"
			remote_shell_cmd = (
				"cd yellow-dev;"
				"./pl.sh;"
				"pushd yellow-client;"
				f"git checkout {client_head};"
				"popd;"
				f"./ci-run.sh true true true true true true true false \"{shard_param}\""
			)
			jobs[executor.submit(run_remote, host, remote_shell_cmd)] = host
		
		for future in as_completed(jobs):
			host = jobs[future]
			ssh_host, output, code = future.result()
			print(f"--- [{ssh_host}] EXIT {code} ---\n{output}\n")

	print("All done.")


if __name__ == '__main__':
	main()
