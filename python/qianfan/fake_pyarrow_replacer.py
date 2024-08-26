import os
import sys
from copy import copy
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder, SourceFileLoader
from types import ModuleType
from typing import Optional, Sequence


def _home_made_module_path_finder(fullname: str) -> str:
    module_parent_path_list = fullname.split(".")
    if len(module_parent_path_list) == 1:
        module_parent_path = fullname
    else:
        module_parent_path = "/".join(module_parent_path_list[:-1])

    for path in sys.path:
        new_path = os.path.join(path, module_parent_path)
        if os.path.exists(new_path):
            return new_path

    raise ImportError(f"cannot find {fullname}")


def _is_pyarrow_installed() -> bool:
    for path in sys.path:
        new_path = os.path.join(path, "pyarrow")
        if os.path.exists(new_path):
            return True

    return False


class _ModuleFinder(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]],
        target: Optional[ModuleType] = None,
    ) -> Optional[ModuleSpec]:
        og_name = fullname

        # 判断导入的包是不是 Pyarrow 的包，且 Pyarrow 没有被安装
        if og_name.startswith("pyarrow") and not _is_pyarrow_installed():
            # 替换掉 name 和 path 为 相关的 Mock 模块信息
            fullname = fullname.replace("pyarrow", "qianfan.utils.fake_pyarrow")
            path = [_home_made_module_path_finder(fullname)]

        module_spec = PathFinder.find_spec(fullname, path, target)
        if not module_spec:
            return None
        module_origin = module_spec.origin
        if not module_origin:
            return None

        if og_name.startswith("pyarrow") and not _is_pyarrow_installed():
            # 使用自定义的 Loader 来加载
            module_spec.loader = _SelfDefinedLoader(og_name, module_origin)

            module_spec.name = og_name
            return module_spec

        return None


class _SelfDefinedLoader(SourceFileLoader):
    def __init__(self, fullname: str, path: str) -> None:
        super().__init__(fullname, path)

    def create_module(self, spec: ModuleSpec) -> Optional[ModuleType]:
        # 如果已经有了就直接复用
        if self.name in sys.modules:
            return sys.modules[self.name]
        # 这里替换一下 name 为 Pyarrow 的模块名
        copy_spec = copy(spec)
        copy_spec.name = self.name
        return super().create_module(copy_spec)

    def exec_module(self, module: ModuleType) -> None:
        super().exec_module(module)
