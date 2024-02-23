import json
import os
import shutil
import time
from glob import glob
import pytest
import papermill as pm

from utils.process_cookbook import ProcessCookbook


@pytest.fixture(scope='session', autouse=True)
def env_set(request):
    if request.config.getoption('--ak') != '':
        os.environ['QIANFAN_ACCESS_KEY'] = request.config.getoption("--ak")
    if request.config.getoption('--sk') != '':
        os.environ['QIANFAN_SECRET_KEY'] = request.config.getoption("--sk")
    if request.config.getoption('--keywords') != '{}':
        os.environ['KEYWORDS_DICT'] = request.config.getoption("--keywords")
    if request.config.getoption('--root-dir') != '':
        os.environ['ROOT_DIR'] = request.config.getoption("--root-dir")
    else:
        os.environ['ROOT_DIR'] = '../../..'

    other_env = [('RetryCount', '3'), ('QIANFAN_QPS_LIMIT', '1'), ('QIANFAN_LLM_API_RETRY_COUNT', '3')]
    for key, value in other_env:
        os.environ[key] = value

    yield
    if os.environ.get('QIANFAN_ACCESS_KEY'):
        del os.environ['QIANFAN_ACCESS_KEY']
    if os.environ.get('QIANFAN_SECRET_KEY'):
        del os.environ['QIANFAN_SECRET_KEY']
    if os.environ.get('KEYWORDS_DICT'):
        del os.environ['KEYWORDS_DICT']
    if os.environ.get('ROOT_DIR'):
        del os.environ['ROOT_DIR']
    for key, value in other_env:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="function")
def const_dir():
    temp_dir = 'test/_temp'
    output_dir = 'test/_output'
    cookbook_dir = 'cookbook'
    root_dir = os.environ['ROOT_DIR']
    const_dir = {
        'cookbook_dir': cookbook_dir,
        'temp_dir': temp_dir,
        'output_dir': output_dir,
        'root_dir': root_dir
    }

    for path in [temp_dir, output_dir]:
        root_path = f'{root_dir}/{path}'
        if os.path.exists(root_path):
            shutil.rmtree(root_path)
        os.makedirs(root_path, exist_ok=True)

    yield const_dir

    for path in [temp_dir, output_dir]:
        root_path = f'{root_dir}/{path}'
        if os.environ.get('DEBUG_MODE', '') == '' and os.path.exists(root_path):
            shutil.rmtree(root_path)


@pytest.mark.skip
@pytest.mark.parametrize(
    "file_reg,params_dict",
    [(
            '**/test_*.ipynb',
            {
                'test_var': "test_value"
            }
    )]
)
def test_demo(file_reg, params_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, **const_dir)


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [  # 分开写的好处是会被单独执行，一个测试有错误不会终止其他测试
        ('batch_prediction.ipynb', {}),
        ('function_call.ipynb', {}),
        ('langchain_sequential.ipynb', {}),
        ('prompt.ipynb', {}),
        ('text2image.ipynb', {}),
        ('hub.ipynb', {}),
        ('**/question_answering.ipynb', {}),
        ('agents/*.ipynb', {}),
        ('function_call.ipynb', {}),

        # ('**/finetune_with_bos_and_evaluate.ipynb', {}),
        # ('eb_search.ipynb', {}),

    ]
)
def test_all(file_reg, params_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, **const_dir)


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [  # 分开写的好处是会被单独执行，一个测试有错误不会终止其他测试
        # ('dataset/dataset101.ipynb', {}),
        # ('dataset/how_to_use_qianfan_operator.ipynb', {}),

        ('dataset/batch_inference_using_dataset.ipynb', {}),
    ]
)
def test_datasets(file_reg, params_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, **const_dir)


# 这个test专门测试含有async的datasets notebook
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        ('dataset/batch_inference_using_dataset.ipynb', {}),
    ]
)
async def test_datasets_async(file_reg, params_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, **const_dir)


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [
        # ('**/semantic_kernel/agent_with_sk.ipynb', {}),
        # ('**/semantic_kernel/chatbot_with_sk.ipynb', {}),
        ('**/semantic_kernel/rag_with_sk.ipynb', {}),
    ]
)
def test_sk(file_reg, params_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, **const_dir)


def template(file_reg, params_dict, root_dir, cookbook_dir, temp_dir, output_dir):
    notebooks = glob(pathname=f'{root_dir}/{cookbook_dir}/{file_reg}', recursive=True)
    params = {}
    params.update(params_dict)
    params.update(json.loads(os.environ.get('KEYWORDS_DICT', '{}')))
    for ipath in notebooks:
        # print(ipath)
        save_path = ipath.replace(f'/{cookbook_dir}/', f'/{temp_dir}/')

        processor = ProcessCookbook(ipath=ipath, save_path=save_path)
        processor.process_branches()
        processor.process_params(params_dict=params)
        processor.save()

    # 执行notebook
    input_path = glob(f'{root_dir}/{temp_dir}/**/*.ipynb', recursive=True)
    output_path = list(map(lambda x: x.replace(temp_dir, output_dir), input_path))

    for ipath, opath in zip(input_path, output_path):
        work_directory = os.path.dirname(ipath).replace(temp_dir, cookbook_dir)
        create_dir([work_directory, os.path.dirname(ipath), os.path.dirname(opath)])
        print(f'执行notebook: {ipath}')
        pm.execute_notebook(ipath, opath, log_output=True, cwd=work_directory)


def create_dir(dir_path_list):
    for dir_path in dir_path_list:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)


def mv_dir(from_dir, to_dir):
    """移动文件夹"""
    if os.path.exists(to_dir):
        shutil.rmtree(to_dir)
    if os.path.exists(from_dir):
        shutil.copytree(from_dir, to_dir)
