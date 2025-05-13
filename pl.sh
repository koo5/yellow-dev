#!/usr/bin/env python3
import os
import shlex
import subprocess

COMMANDS = ["eg 'git checkout main'", "gpl", "eg 'git checkout main'"]

ENV = os.environ.copy()
ENV["PYTHONUNBUFFERED"] = "1"
outputs = []

def toilet(text):
  subprocess.run(shlex.split('toilet -s -f future') + [text])

for cmd in COMMANDS:
  toilet(cmd)
  SHELL = ["fish", "-c", cmd]
  output_lines = []

  with subprocess.Popen(
          SHELL,
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,   # merge stderr → stdout
          text=True,
          bufsize=1,                  # line‑buffered
          env=ENV
  ) as proc:
      for line in proc.stdout:        # stream live
          print(line, end="")         # 1) immediate console
          output_lines.append(line)   # 2) accumulate
      proc.wait()                     # propagate exit code if needed

  output = "".join(output_lines)
  outputs.append((cmd, output))

prompt = f"""'eg' is an alias for running the argument as a command in every git submodule.
'gpl' is an alias for 'git pull'. I run a sequence of commands. First i pull every submodule, then i pull the main repo, then i makes sure each submodule points to the latest main again. Review the series of outputs and answer with OK or by pointing out any indicated issues, things to be aware of regarding the indicated state of the repositories, or anything unexpected. Stay very concise. If you notice issues, limit your answer to bullet-points. I am a git expert and I know what I am doing. I am not looking for a summary of the output or tips, but rather for issues pointed out by the outputs. """


for cmd, output in outputs:
  prompt += f"""
<COMMAND {cmd} OUTPUT>
{output}
</COMMAND {cmd} OUTPUT>
"""

print()
#print(prompt)
toilet("Prompting LLM...")
subprocess.run(["llm", prompt], env=ENV)
