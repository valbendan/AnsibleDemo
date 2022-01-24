import json
import os.path
import subprocess

import typer


def main(out_dir: str = typer.Argument(..., help="输出目录")):
    """
    获取 Ansible 所有模块的文档
    """
    process = subprocess.run(["ansible-doc", "-l", "-j"], capture_output=True)
    out = json.loads(process.stdout)

    for module in out.keys():
        typer.secho(f"<<< get {module=} doc", fg="green")
        process = subprocess.run(["ansible-doc", module, "-j"], capture_output=True)
        doc = json.loads(process.stdout)
        with open(os.path.join(out_dir, f"{module}.json"), "w") as fp:
            json.dump(doc, fp, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    typer.run(main)
