import json
import os
import shutil
import time
from glob import glob
from typing import Dict

import papermill as pm

from cookbook_process import CookbookProcessor


class CookbookExecutor:
    debug: bool = False
    const_dir: Dict[str, str] = {}

    def __init__(self, temp_dir: str = 'test/_temp', output_dir: str = 'test/_output',
                 cookbook_dir: str = 'cookbook', root_dir: str = None):
        # 生成运行日期时间字符串，用于区分不同测试用例
        time.sleep(1)
        time_str = time.strftime("%Y%m%d_%H:%M:%S", time.localtime())
        self.const_dir = {
            'temp_dir': f'{temp_dir}={time_str}',
            'output_dir': f'{output_dir}={time_str}',
            'cookbook_dir': cookbook_dir,
            'root_dir': os.environ['ROOT_DIR'] if root_dir is None else root_dir
        }

    def __enter__(self):
        for path in [self.const_dir['temp_dir'], self.const_dir['output_dir']]:
            self.rm_dir(path, mkdir=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for path in [self.const_dir['temp_dir'], self.const_dir['output_dir']]:
            if not self.debug:
                self.rm_dir(path)

    def rm_dir(self, path: str, mkdir: bool = False):
        root_path = f'{self.const_dir["root_dir"]}/{path}'
        if os.path.exists(root_path):
            shutil.rmtree(root_path)
        if mkdir:
            os.makedirs(root_path, exist_ok=True)

    def run(self, debug=False):
        self.debug = debug
        # 执行notebook
        for tpath, opath, wkdir in self.prepare_dir():
            print(f'执行notebook: {tpath}')
            pm.execute_notebook(tpath, opath, log_output=True, cwd=wkdir)

    def prepare(self, file_reg, params_dict):
        notebooks = glob(pathname=f'{self.const_dir["root_dir"]}/{self.const_dir["cookbook_dir"]}/{file_reg}',
                         recursive=True)
        params = {**params_dict}
        params.update(json.loads(os.environ.get('KEYWORDS_DICT', '{}')))
        for cpath in notebooks:
            save_path = cpath.replace(f'/{self.const_dir["cookbook_dir"]}/', f'/{self.const_dir["temp_dir"]}/')

            processor = CookbookProcessor(cpath=cpath, save_path=save_path)
            processor.process_branches()
            processor.process_params(params_dict=params)
            processor.save()

    def prepare_dir(self):
        temp_path = glob(f'{self.const_dir["root_dir"]}/{self.const_dir["temp_dir"]}/**/*.ipynb', recursive=True)
        output_path, work_directory = [], []

        for tpath in temp_path:
            output_path.append(tpath.replace(self.const_dir["temp_dir"], self.const_dir["output_dir"]))
            work_directory.append(
                os.path.dirname(tpath).replace(
                    self.const_dir["temp_dir"], self.const_dir["cookbook_dir"]
                )
            )

        for tpath, opath, wkdir in zip(temp_path, output_path, work_directory):
            os.makedirs(os.path.dirname(tpath), exist_ok=True)
            os.makedirs(os.path.dirname(opath), exist_ok=True)
            os.makedirs(wkdir, exist_ok=True)

        return zip(temp_path, output_path, work_directory)
