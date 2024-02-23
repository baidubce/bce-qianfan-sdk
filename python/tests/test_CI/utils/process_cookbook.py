import os
import random
import re
import string
from typing import Dict, List, Any, Union
import logging
import nbformat as nbf
from pydantic import BaseModel, Field


class ProcessCookbook(BaseModel):
    ntbk_branches: Dict[str, nbf.NotebookNode] = Field(default={'main': nbf.v4.new_notebook()})
    kernel_spec: Dict[str, str] = Field(default={})
    ipath: str = Field(default=...)
    save_path: str = Field(default=...)

    class Config:
        arbitrary_types_allowed = True

    def process_branches(self):
        ntbk = nbf.read(self.ipath, nbf.NO_CONVERT)
        self.kernel_spec.update(ntbk.metadata.get('kernelspec', {}))

        for cell in ntbk.cells:
            self.clean_env(cell)
            self.check_cells(cell)

    def check_cells(self, cell):
        source, cell_tags, cell_type = self.get_cell_info(cell)
        if 'cell_skip' in cell_tags:
            logging.info(f'skip cell')
            return

        branch_tags = filter(lambda tag: tag.startswith('branch_'), cell_tags)

        is_main = True
        for tag in branch_tags:
            self.split_branch(cell, tag)
            is_main = False
        if is_main or 'branch_main' in cell_tags:
            logging.info(f'add cell to branch main')
            self.ntbk_branches['main']['cells'].append(self.generate_cell(cell))
            if self.ntbk_branches['main'].metadata.get('kernelspec', {}) == {}:
                self.ntbk_branches['main'].metadata['kernelspec'] = self.kernel_spec

    @staticmethod
    def get_cell_info(cell) -> tuple[str, list, str]:
        source = cell['source']
        cell_tags = cell.get('metadata', {}).get('tags', [])
        cell_type = cell['cell_type']

        if source.startswith('#-#'):
            tag_line = source.split('\n')[0].replace('#-#', '')
            cell_tags.extend([src_tag.strip() for src_tag in tag_line.split(' ') if src_tag not in cell_tags])

        return source, cell_tags, cell_type

    def split_branch(self, cell, tag):
        if tag not in self.ntbk_branches:
            logging.info(f'create branch {tag}')
            self.ntbk_branches[tag] = nbf.v4.new_notebook(
                cells=self.copy_cells(self.ntbk_branches['main']['cells'])
            )
            self.ntbk_branches[tag].metadata['kernelspec'] = self.kernel_spec

        logging.info(f'add cell to branch {tag}')
        self.ntbk_branches[tag]['cells'].append(
            self.generate_cell(cell)
        )

    def generate_cell(self, cell):
        source, cell_tags, cell_type = self.get_cell_info(cell)
        if cell_type == 'markdown':
            func = nbf.v4.new_markdown_cell
        elif cell_type == 'code':
            func = nbf.v4.new_code_cell
        else:
            func = nbf.v4.new_raw_cell
        if len(cell_tags) > 0:
            return func(source, metadata={'tags': cell_tags})
        else:
            return func(source)

    def copy_cells(self, cells):
        result_cells = []
        for cell in cells:
            result_cells.append(self.generate_cell(cell))
        return result_cells

    def process_params(self, params_dict={}, branches: List[str] = None):
        if branches is None:  # 全部分支
            branches = list(self.ntbk_branches.keys())
        else:  # 指定分支
            branches = [branch for branch in branches if branch in self.ntbk_branches]

        for branch in branches:
            for cell in self.ntbk_branches[branch].cells:
                params = self.find_parameters(cell, params_dict)
                self.inject_parameters(cell, params)

    def find_parameters(self, cell, params_dict):
        _, cell_tags, _ = self.get_cell_info(cell)

        random_params_list = [x.replace('random_', '') for x in cell_tags if x.startswith('random_')]
        # params_list = [x.replace('parameter_', '') for x in cell_tags if x.startswith('parameter_')]

        random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        params = {param: value for param, value in params_dict.items()}
        random_params = {random_param: f'{random_param}_{random_str}' for random_param in random_params_list}
        params.update(random_params)

        return params

    @staticmethod
    def inject_parameters(cell, params):
        def re_params(text, param, param_value):
            re_str1 = r"({})\s*=\s*\S+".format(param)  # 赋值表达式的参数： 参数 = "参数值"
            re_str2 = r'[\'\"]\s*{}\s*[\'\"]'.format(param)  # 字符串格式的参数： "参数"
            new_text = re.sub(re_str1, f'\g<1> = "{param_value}"', text, flags=re.M)
            new_text = re.sub(re_str2, f'"{param_value}"', new_text, flags=re.M)
            return new_text

        def re_random(text):
            re_str1 = r'random_([^\'\"\s\[\]\(\)]+)\s*=\s*\S+'  # 赋值表达式的参数： 参数 = "参数值"
            re_str2 = r'[\'\"]\s*random_([^\'\"\s]+)\s*[\'\"]'  # 字符串格式的参数： "参数"
            random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            new_text = re.sub(re_str1, f'random_\g<1> = "\g<1>_{random_str}"', text, flags=re.M)
            new_text = re.sub(re_str2, f'"\g<1>_{random_str}"', new_text, flags=re.M)
            return new_text

        # 注入参数
        source = cell['source']
        # 给定参数
        for param, param_value in params.items():
            source = re_params(source, f'{param}', param_value)

        cell['source'] = re_random(source)

    @staticmethod
    def clean_env(cell):
        if cell.cell_type == 'code' and cell.get('source'):
            pat_group = '|'.join(
                ['QIANFAN_ACCESS_KEY', 'QIANFAN_SECRET_KEY', "KEYWORDS_DICT", "ROOT_DIR", "QIANFAN_AK", "QIANFAN_SK"])
            source = cell['source']

            pat_l, pat_r = r'(os.environ\[[\'\"])', r'([\'\"]\])'
            pat_str = pat_l + f'((?:{pat_group}))' + pat_r
            re_str = r'\g<1>\g<2>\g<3>'

            source = re.sub(f'#[ ]*{pat_str}', re_str, source)
            source = re.sub(f'{pat_str}', f'# {re_str}', source)
            cell['source'] = source

    def save(self):
        for branch, branch_bn in self.ntbk_branches.items():
            with open(self.get_save_path(branch), 'w') as f:
                nbf.write(branch_bn, fp=f)

    def get_save_path(self, branch):
        logging.info(f'save to {self.save_path}')

        save_dir = os.path.dirname(self.save_path)
        os.makedirs(save_dir, exist_ok=True)

        origin_basename = os.path.basename(self.ipath)
        branch_save_path = self.save_path.replace(origin_basename, f'{branch}_{origin_basename}')
        return branch_save_path
