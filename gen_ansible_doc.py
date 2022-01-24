import json
import subprocess

import typer


def main():
    process = subprocess.run(["ansible-doc", "-l", "-j"], capture_output=True)
    out = json.loads(process.stdout)
    print(out.keys())


if __name__ == "__main__":
    typer.run(main)
