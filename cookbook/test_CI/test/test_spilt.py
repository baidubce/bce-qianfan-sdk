import json
import os
import shutil
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
    if request.config.getoption('--keywords') != '':
        os.environ['KEYWORDS_DICT'] = request.config.getoption("--keywords")

    os.environ['ROOT_DIR'] = request.config.getoption("--root-dir")
    os.environ['ROOT_DIR'] = '../../..'

    yield
    if os.environ.get('QIANFAN_ACCESS_KEY'):
        del os.environ['QIANFAN_ACCESS_KEY']
    if os.environ.get('QIANFAN_SECRET_KEY'):
        del os.environ['QIANFAN_SECRET_KEY']
    if os.environ.get('KEYWORDS_DICT'):
        del os.environ['KEYWORDS_DICT']
    if os.environ.get('ROOT_DIR'):
        del os.environ['ROOT_DIR']

@pytest.fixture(scope="module")
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
        if os.path.exists(root_path):
            shutil.rmtree(root_path)

@pytest.fixture(scope="module")
def keywords_dict():
    keywords = os.environ['KEYWORDS_DICT']
    # 读取json字符串api_key
    keywords_dict = json.loads(keywords)
    return keywords_dict

@pytest.mark.parametrize(
    "file_reg,params_dict",
    [(
            '**/test_*.ipynb',
            {
            }
    )]
)
def test_demo(file_reg, params_dict, keywords_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, keywords_dict=keywords_dict, **const_dir)


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [(
            '**/function_call*.ipynb',
            {
            }
    )]
)
def test_function_call(file_reg, params_dict, keywords_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, keywords_dict=keywords_dict, **const_dir)


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [(
            '**/question_answering.ipynb',
            {
            }
    )]
)
def test_qa(file_reg, params_dict, keywords_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, keywords_dict=keywords_dict, **const_dir)


@pytest.mark.skip
@pytest.mark.parametrize(
    "file_reg,params_dict",
    [(
            '**/finetune_with_bos_and_evaluate.ipynb',
            {
                # 'bos_bucket_name': "sdk-test",
                # 'bos_bucket_file_path': "dataset_test",
                # 'model_version_id': "amv-m8zsti7kf2x3",
                # 'user_app_id': 26217442
            }
    )]
)
def test_dataset_bos(file_reg, params_dict, keywords_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, keywords_dict=keywords_dict, **const_dir)


@pytest.mark.parametrize(
    "file_reg,params_dict",
    [(
            '**/batch_prediction.ipynb',
            {
            }
    )]
)
def test_batch_pred(file_reg, params_dict, keywords_dict, const_dir):
    template(file_reg=file_reg, params_dict=params_dict, keywords_dict=keywords_dict, **const_dir)


def template(file_reg, params_dict, keywords_dict, root_dir, cookbook_dir, temp_dir, output_dir):
    notebooks = glob(pathname=f'{root_dir}/{cookbook_dir}/{file_reg}', recursive=True)
    params = {}
    params.update(params_dict)
    params.update(keywords_dict)
    print(params)
    for ipath in notebooks:
        print(ipath)
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
