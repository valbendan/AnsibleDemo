import json
import os.path
import subprocess
from json import JSONDecodeError
from typing import List, Dict, Union

import typer
from pydantic import Field, BaseModel


class AnsibleModuleOption(BaseModel):
    aliases: List[str] = Field([])
    description: List[str] = Field([])
    typ_: str = Field("str", alias="type")
    required: bool = Field(False)
    default: Union[str, int, bool, list, dict] = Field(None)
    choices: List[Union[str, int]] = Field([])
    elements: str = Field("")
    version_added: str = Field("")
    suboptions: Dict[str, "AnsibleModuleOption"] = Field(dict())

    def dict(self, **kwargs):
        ret = super().dict(**kwargs)
        if ret["default"] is None:
            ret["default"] = ""
        ret["default"] = str(ret["default"])
        ret["choices"] = [str(ch) for ch in ret["choices"]]
        return ret


class AnsibleModuleDoc(BaseModel):
    author: Union[str, List[str]] = Field([])
    collection: str = Field(...)
    description: Union[str, List[str]] = Field([])
    has_action: bool = Field(False)
    module: str = Field(...)
    notes: Union[str, List[str]] = Field([])
    options: Dict[str, AnsibleModuleOption] = Field(dict())
    requirements: List[str] = Field([])
    short_description: str = Field("")
    version_added: str = Field("")

    def dict(self, **kwargs):
        data = super().dict(**kwargs)
        if isinstance(data["description"], str):
            data["description"] = [data["description"]]
        if isinstance(data["notes"], str):
            data["notes"] = [data["notes"]]
        if isinstance(data["author"], str):
            data["author"] = [data["author"]]
        return data


class AnsibleModuleReturn(BaseModel):
    description: str = Field("")
    returned: str = Field("")
    typ_: str = Field("", alias="type")
    elements: str = Field("")
    sample: str = Field("")
    version_added: str = Field("")
    contains: Dict[str, "AnsibleModuleReturn"] = Field(dict())


class AnsibleModuleDocumentation(BaseModel):
    doc: AnsibleModuleDoc = Field(...)
    examples: str = Field("")
    ret: Dict[str, AnsibleModuleReturn] = Field(dict())


def gen_module_doc(module: str) -> Dict[str, dict]:
    """
    We should normalize the output of Asnible Module documentation

    Since Java/Kotlin process dynamic type is hard
    """
    process = subprocess.run(["ansible-doc", module, "-j"], capture_output=True)
    try:
        data = json.loads(process.stdout)
        assert isinstance(data, dict)
        name = list(data.keys())[0]
        value = list(data.values())[0]
        return {name: AnsibleModuleDocumentation(**value).dict()}
    except JSONDecodeError as e:
        typer.secho(f"<<< {module=} json decode failed: {e}", fg="red")
        return dict()
    except Exception as e:
        typer.secho(f"<<< {module=} pydantic ?? failed: {e}", fg="red")
        return dict()


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
            collection_name = (
                "global.stub"  # indeed, global is not exists, it's just a stub file
            )

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
