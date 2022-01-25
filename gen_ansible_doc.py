import json
import os.path
import subprocess
from typing import List, Dict

import typer


def gen_module_doc(module: str) -> Dict[str, dict]:
    process = subprocess.run(["ansible-doc", module, "-j"], capture_output=True)
    return json.loads(process.stdout)


def group_to_collections(all_modules: List[str]) -> Dict[str, List[str]]:
    """
    使用 Ansible Collections 对 module 进行分组
    :param all_modules:
    :return: collection_name -> collections moduls
    """
    group = dict()
    for module in all_modules:
        try:
            collection_name, _ = module.rsplit(".", 1)
        except ValueError:
            collection_name = 'global.stub'  # indeed, global is not exists, it's just a stub file

        if collection_name in group:
            group[collection_name].append(module)
        else:
            group[collection_name] = [module]
    return group


def main(out_dir: str = typer.Argument(..., help="输出目录")):
    """
    获取 Ansible 所有模块的文档

    按照 collections 分组存储到指定的目录中

    使用 Github Action ansible_doc.yml 运行
    """
    process = subprocess.run(["ansible-doc", "-l", "-j"], capture_output=True)
    out = json.loads(process.stdout)

    collection_modules = group_to_collections(out.keys())

    for collection, modules in collection_modules.items():
        data = dict()
        for module in modules:
            typer.secho(f"<<< get {module=} doc", fg="green")
            data |= gen_module_doc(module)
        with open(os.path.join(out_dir, f"{collection}.json"), "w") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    typer.run(main)
