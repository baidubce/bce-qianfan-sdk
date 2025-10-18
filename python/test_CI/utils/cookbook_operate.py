# Copyright (c) 2023 Baidu, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
    utils for cookbook tests
"""

import json
import logging
import os
import random
import re
import shutil
import string
import time
from glob import glob
from typing import Dict, List

import nbformat as nbf
import papermill as pm
from pydantic import BaseModel, Field


class CookbookProcessor(BaseModel):
    """
    预处理Notebook的类
    """

    ntbk_branches: Dict[str, nbf.NotebookNode] = Field(default={})
    kernel_spec: Dict[str, str] = Field(default={})
    ntbk: nbf.NotebookNode = Field(default=...)

    class Config:
        """
        pydantic配置类
        """

        arbitrary_types_allowed = True

    def process_branches(self):
        """
        处理分支代码块。

        Args:
            self (CookbookProcessor): 当前CookbookProcessor对象。

        Returns:
            None

        """
        self.kernel_spec.update(self.ntbk.metadata.get("kernelspec", {}))

        for cell in self.ntbk.cells:
            self.clean_env(cell)
            self.check_cells(cell)

    def check_cells(self, cell):
        """
        检查cell是否需要跳过，并处理分支cell。

        Args:
            cell (nbformat.notebooknode.NotebookNode): 需要检查的cell。

        Returns:
            None
        """
        source, cell_tags, cell_type = self.get_cell_info(cell)
        if "cell_skip" in cell_tags:
            logging.info(f"skip cell")
            return

        branch_tags = filter(lambda tag: tag.startswith("branch_"), cell_tags)

        is_main = True
        for tag in branch_tags:
            self.split_branch(cell, tag)
            is_main = False
        if is_main or "branch_main" in cell_tags:
            logging.info(f"add cell to branch main")
            if self.ntbk_branches.get("main", None) is None:
                self.ntbk_branches["main"] = nbf.v4.new_notebook(cells=[])
            self.ntbk_branches["main"]["cells"].append(self.generate_cell(cell))
            if self.ntbk_branches["main"].metadata.get("kernelspec", {}) == {}:
                self.ntbk_branches["main"].metadata["kernelspec"] = self.kernel_spec

    @staticmethod
    def get_cell_info(cell) -> tuple[str, list, str]:
        """
        获取单个cell的信息。

        Args:
            cell (dict): 一个cell的信息，包含'source', 'metadata', 'cell_type'等键值对。

        Returns:
            tuple[str, list, str]: 一个元组，包含source、cell_tags和cell_type三个元素。
                - source (str): cell的内容文本信息。
                - cell_tags (list): cell的标签信息，以列表形式返回。
                - cell_type (str): cell的类型。
        """
        source = cell["source"]
        cell_tags = cell.get("metadata", {}).get("tags", [])
        cell_type = cell["cell_type"]

        if source.startswith("#-#"):
            tag_line = source.split("\n")[0].replace("#-#", "")
            cell_tags.extend([
                src_tag.strip()
                for src_tag in tag_line.split(" ")
                if src_tag not in cell_tags
            ])

        return source, cell_tags, cell_type

    def split_branch(self, cell, tag: str):
        """
        将给定的cell添加到指定分支的notebook中。

        Args:
            cell (nbformat.notebooknode.NotebookNode): 要添加的cell。
            tag (str): 分支名称。

        Returns:
            None
        """
        if tag not in self.ntbk_branches:
            logging.info(f"create branch {tag}")
            self.ntbk_branches[tag] = nbf.v4.new_notebook(
                cells=self.copy_cells(self.ntbk_branches["main"]["cells"])
            )
            self.ntbk_branches[tag].metadata["kernelspec"] = self.kernel_spec

        logging.info(f"add cell to branch {tag}")
        self.ntbk_branches[tag]["cells"].append(self.generate_cell(cell))

    def generate_cell(self, cell):
        """
        生成单元格拷贝

        Args:
            cell (dict): 单元格信息，包含以下键值：
                - source (str): 单元格内容
                - cell_tags (list[str]): 单元格标签列表
                - cell_type (str): 单元格类型，可选值为'markdown'、'code'、'raw'

        Returns:
            nbformat单元格对象，类型为nbformat单元格类型对应的类实例

        """
        source, cell_tags, cell_type = self.get_cell_info(cell)
        if cell_type == "markdown":
            func = nbf.v4.new_markdown_cell
        elif cell_type == "code":
            func = nbf.v4.new_code_cell
        else:
            func = nbf.v4.new_raw_cell
        if len(cell_tags) > 0:
            return func(source, metadata={"tags": cell_tags})
        else:
            return func(source)

    def copy_cells(self, cells):
        """
        复制给定的单元格列表，并返回一个新的单元格列表。

        Args:
            cells (list): 需要复制的单元格列表。

        Returns:
            list: 包含复制后的单元格的新列表。
        """
        result_cells = []
        for cell in cells:
            result_cells.append(self.generate_cell(cell))
        return result_cells

    def process_params(self, params_dict={}, branches: List[str] = None):
        """
        遍历给定分支的单元，并根据给定的参数字典向单元中注入参数。

        Args:
            params_dict (dict): 参数字典，用于查找和注入参数。
            branches (List[str], optional): 需要处理的分支列表，默认为None表示处理所有分支。

        Returns:
            None: 无返回值，但会将参数注入到相应的单元中。
        """
        if branches is None:  # 全部分支
            branches = list(self.ntbk_branches.keys())
        else:  # 指定分支
            branches = [branch for branch in branches if branch in self.ntbk_branches]

        for branch in branches:
            for cell in self.ntbk_branches[branch].cells:
                params = self.find_parameters(cell, params_dict)
                self.inject_parameters(cell, params)

    def find_parameters(self, cell, params_dict):
        """
        为传入的参数生成随机的参数名称并返回

        Args:
            cell: 需要填充参数的单元
            params_dict: 参数名称和值的字典

        Returns:
            返回填充了随机参数名称的字典
        """
        _, cell_tags, _ = self.get_cell_info(cell)

        random_params_list = [
            x.replace("random_", "") for x in cell_tags if x.startswith("random_")
        ]
        # params_list = [x.replace('parameter_', '') for x in cell_tags if x.startswith('parameter_')]

        random_str = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        params = {param: value for param, value in params_dict.items()}
        random_params = {
            random_param: f"{random_param}_{random_str}"
            for random_param in random_params_list
        }
        params.update(random_params)

        return params

    @staticmethod
    def inject_parameters(cell, params):
        """
        Inject parameters into the source code of a cell.

        Args:
            cell (dict): A dictionary containing the cell's source code.
            params (dict): A dictionary containing the parameters to inject.

        Returns:
            None
        """

        def re_params(text, param, param_value):
            """
            将文本中的参数替换为指定的参数值。

            Args:
                text (str): 需要替换的文本。
                param (str): 需要替换的参数名。
                param_value (Any): 参数的新值，可以是任意类型。

            Returns:
                str: 替换后的文本。

            """
            re_str1 = r"({})\s*=\s*\S+".format(
                param
            )  # 赋值表达式的参数： 参数 = "参数值"
            re_str2 = r"[\'\"]\s*{}\s*[\'\"]".format(param)  # 字符串格式的参数： "参数"
            re_type = r'"{}"' if isinstance(param_value, str) else r"{}"
            new_text = re.sub(
                re_str1, r"\g<1> = " + re_type.format(param_value), text, flags=re.M
            )
            new_text = re.sub(
                re_str2, re_type.format(param_value), new_text, flags=re.M
            )
            return new_text

        def re_random(text):
            """
            在文本中替换所有random开头的字符串为随机字符串，并替换赋值表达式的参数。

            Args:
                text (str): 需要替换的文本。

            Returns:
                str: 替换后的文本。

            """
            re_str1 = r"random_([^\'\"\s\[\]\(\)]+)\s*=\s*\S+"  # 赋值表达式的参数： 参数 = "参数值"
            re_str2 = (
                r"[\'\"]\s*random_([^\'\"\s]+)\s*[\'\"]"  # 字符串格式的参数： "参数"
            )
            random_str = "".join(
                random.choices(string.ascii_letters + string.digits, k=5)
            )
            new_text = re.sub(
                re_str1, f'random_\g<1> = "\g<1>_{random_str}_"', text, flags=re.M
            )
            new_text = re.sub(re_str2, f'"\g<1>_{random_str}_"', new_text, flags=re.M)
            return new_text

        # 注入参数
        source = cell["source"]
        # 给定参数
        for param, param_value in params.items():
            source = re_params(source, f"{param}", param_value)

        cell["source"] = re_random(source)

    @staticmethod
    def clean_env(cell):
        """
        注释掉notebook的指定环境变量，接管到CI环境。

        Args:
            cell (dict): notebook cell 字典对象。

        Returns:
            None
        """
        if cell["cell_type"] == "code" and cell.get("source"):
            pat_group = "|".join([
                "QIANFAN_ACCESS_KEY",
                "QIANFAN_SECRET_KEY",
                "KEYWORDS_DICT",
                "ROOT_DIR",
                "QIANFAN_AK",
                "QIANFAN_SK",
            ])
            source = cell["source"]

            pat_l, pat_r = r"(os.environ\[[\'\"])", r"([\'\"]\])"
            pat_str = pat_l + f"((?:{pat_group}))" + pat_r
            re_str = r"\g<1>\g<2>\g<3>"

            source = re.sub(f"^# *{pat_str}", re_str, source, flags=re.M)
            source = re.sub(f"^{pat_str}", f"# {re_str}", source, flags=re.M)
            cell["source"] = source


class CookbookManager:
    """
    管理cookbook路径保存的类
    """

    cpath: str
    save_path: str
    processor: CookbookProcessor

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, cpath: str, save_path: str):
        self.cpath = cpath
        self.save_path = save_path
        self.processor = CookbookProcessor(ntbk=nbf.read(self.cpath, nbf.NO_CONVERT))
        self.process_branches = self.processor.process_branches
        self.process_params = self.processor.process_params

    def save(self):
        """
        保存所有分支的notebook

        Args:
            self (CookbookManager): CookbookManager对象。

        Returns:
            None

        """
        path_map = {}
        work_dir = os.path.dirname(self.cpath)
        for branch, branch_bn in self.processor.ntbk_branches.items():
            branch_path = self.get_save_path(branch)
            branch_name = os.path.basename(branch_path)
            path_map[branch_name] = work_dir
            with open(branch_path, "w") as f:
                nbf.write(branch_bn, fp=f)
        return path_map

    def get_save_path(self, branch_name: str):
        """
        获取分支保存路径。

        Args:
            branch_name (str): 分支名称。

        Returns:
            str: 分支保存路径。

        """
        logging.info(f"save to {self.save_path}")
        origin_basename = os.path.basename(self.cpath)
        return f"{self.save_path}/{branch_name}_{origin_basename}"


class CookbookExecutor:
    """
    提供notebook运行环境的类
    """

    debug: bool = False
    const_dir: Dict[str, str] = {}
    path_map: Dict[str, str] = {}

    def __init__(self, root_dir: str):
        """
        Args:
            root_dir (str, optional): 根目录路径，默认为None。

        Returns:
            None

        """
        root_dir = os.path.abspath(root_dir)
        temp_dir = f"{root_dir}/test/temp"
        output_dir = f"{root_dir}/test/output"
        cookbook_dir = f"{root_dir}/cookbook"

        self.const_dir = {
            "root_dir": root_dir,
            "temp_dir": self.time_dir(temp_dir),
            "output_dir": self.time_dir(output_dir),
            "cookbook_dir": cookbook_dir,
        }

    @staticmethod
    def time_dir(prefix):
        """
        获取当前时间字符串，用于区分不同测试用例。
        Args:
            prefix (str): 附加的前缀。
        Returns:
            str: 时间字符串。
        """
        time.sleep(1)
        time_str = time.strftime("%Y%m%d_%H:%M:%S", time.localtime())
        return f"{prefix}={time_str}"

    def __enter__(self):
        """
        当使用with语句时，进入上下文时的函数。

        Args:
            无。

        Returns:
            self: 返回当前对象本身。

        """
        self.rm_dir(self.const_dir["temp_dir"], mkdir=True)
        self.rm_dir(self.const_dir["output_dir"], mkdir=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        with退出时执行清理工作。

        Args:
            exc_type (Type): 异常类型
            exc_val (Any): 异常值
            exc_tb (TracebackType): 异常回溯信息

        Returns:
            None

        """

        self.rm_dir(self.const_dir["temp_dir"])
        if not self.debug:
            self.rm_dir(self.const_dir["output_dir"])
        if len(os.listdir(f'{self.const_dir["root_dir"]}/test')) == 0:
            os.rmdir(f'{self.const_dir["root_dir"]}/test')

    def rm_dir(self, path: str, mkdir: bool = False):
        """
        删除指定路径下的文件夹

        Args:
            path (str): 文件夹路径
            mkdir (bool, optional): 是否在删除后重新创建文件夹.

        Returns:
            None
        """
        if os.path.exists(path):
            shutil.rmtree(path)
        if mkdir:
            os.makedirs(path, exist_ok=True)

    def run(self, debug=False):
        """
        执行notebook

        Args:
            debug (bool, optional): 是否开启调试模式，该模式会保留中间文件，默认为False.

        Returns:
            None
        """
        self.debug = debug
        # 执行notebook
        for tpath, opath, wkdir in self.prepare_dir():
            print(f"\nworking: \n    {tpath}\n -> {opath}\n in {wkdir}\n")
            pm.execute_notebook(tpath, opath, log_output=True, cwd=wkdir)

    def find(self, file_reg, default_fd) -> List[str]:
        """
        查找指定文件路径。
        Args:
            file_reg (str):
                文件模式，用于匹配所有需要处理的Cookbook文件。
                支持单文件、单文件夹、unix通配符
            default_fd (bool): True表示使用项目根目录相对路径，False则为当前目录相对路径
        Returns:
            list: 文件路径列表。
        """
        find_dir = self.const_dir["cookbook_dir"] if default_fd else os.getcwd()

        if file_reg.endswith("/"):
            file_reg = file_reg[:-1]
        if not os.path.isabs(file_reg):
            file_reg = f"{find_dir}/{file_reg}"
        if os.path.isdir(file_reg):
            file_reg = f"{file_reg}/**/*.ipynb"
        file_list = glob(pathname=file_reg, recursive=True)
        file_list = [file for file in file_list if file.endswith(".ipynb")]
        if len(file_list) == 0:
            logging.warning(f"没有找到匹配的Cookbook文件: {file_reg}")
        return file_list

    def prepare(self, file_reg, params_dict, default_fd=True):
        """
        准备函数，用于处理Cookbook。

        Args:
            file_reg (str): 文件模式，用于匹配所有需要处理的Cookbook文件。
            params_dict (dict): 参数字典，用于更新全局参数。
            default_fd (bool): True表示使用项目根目录相对路径，False则为当前目录相对路径

        Returns:
            None
        """
        params = {**params_dict}
        params.update(json.loads(os.environ.get("KEYWORDS_DICT", "{}")))
        for cpath in self.find(file_reg, default_fd):
            save_path = self.const_dir["temp_dir"]

            manager = CookbookManager(cpath=cpath, save_path=save_path)
            manager.process_branches()
            manager.process_params(params_dict=params)
            self.path_map.update(manager.save())

    def prepare_dir(self):
        """
        创建临时目录.

        Args:
            None.

        Returns:
            temp_path (list): 临时文件路径列表。
            output_path (list): 输出文件路径列表。
            work_directory (list): 工作目录列表。
        """
        temp_path = glob(f'{self.const_dir["temp_dir"]}/*.ipynb', recursive=True)

        output_path, work_directory = [], []
        for tpath in temp_path:
            file_name = os.path.basename(tpath)
            output_path.append(os.path.join(self.const_dir["output_dir"], file_name))
            work_directory.append(self.path_map[file_name])

        path_zip = zip(temp_path, output_path, work_directory)
        return path_zip
