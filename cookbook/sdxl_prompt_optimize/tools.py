from qianfan.common import Prompt
from qianfan import Text2Image,Completion
from PIL import Image 
import io,os,qianfan
import matplotlib.pyplot as plt
import numpy as np



# 优化任务函数, 输入为字符串
def prompt_update(pt):
    # 优化任务描述
    mission = """
    你的任务是将[输入prompt]进行优化,返回一个[输出prompt],以指导Stable-Diffusion模型创建精致准确的图像。你需要做如下几件事:
    1.发挥想象力,在理解输入prompt的真实含义的基础上,为[输出prompt]添加视觉细节描述和场景背景补充,提高图像质量和真实感。视觉细节可以包括物体的材质、纹理、光影等;场景背景可以是环境布置、时间状态等。
    2.将输入prompt中的关键词或短语翻译为英文,并注意处理词语的文化内涵和隐喻。如果是常见物体,可使用其官方英文描述,像"夫妻肺片"翻译为"sliced beef with beef offal"。
    3.在[输出prompt]中,首先描述主体部分,然后是次要部分。对于多个主体,可根据重要程度分配不同权重,主体权重高于次要部分。权重可用括号表示,如(subject:1.3)。
    4.在[输出prompt]中添加一些相关的描述，比如 (8k, highly detailed, professional, trending on artstation, unreal engine, high-resolution scan, realistic landscape, shadow, HDR)，或者其他你认为有助于描述图像的词语。
    5.在[输出prompt]最后给出相应的negative prompt，它是一些与图像主题不相关或者有冲突的描述。
    6.[输出prompt]的长度不应超过50个词。
    示例：
    [示例1]:
    [输入prompt]: “蚂蚁上树”。
    [输出prompt]: “Sauteed vermicelli with minced pork, rich soy-based sauce, garnished with chopped scallions, vibrant colors, photorealistic, food photography, close-up shot, richly textured, steaming hot, appetizing, culinary presentation, (detailed garnish:1.3), high resolution, 8k, HDR, natural lighting
                Negative prompt: text, logos, watermarks, out of frame, unattractive, discolored, unappetizing, messy, artificial, poorly lit”
    [示例2]:
    [输入prompt]: "一只高贵的柯基犬，素描画风格”。
    [输出prompt]: “Noble Corgi, sketch style, detailed line work, elegant, artistic, black and white, portrait, (intricate details:1.3), high resolution, 8k
                Negative prompt: text, logos, watermarks, out of frame, messy, blurry, extra limbs.” 
    [示例3]:
    [输入prompt]:"金发维京女人"
    [输出prompt]:" a beautiful fashion blond viking woman, revealing outfit, symmetrical, maximalist, lily frame, art by ilya kuvshinov, rossdraws, sharp focus, art by wlop and artgerm,  extreme detail, detailed drawing, hyper detailed face
                Negative prompt: text, logos, watermarks, out of frame, unattractive, discolored, unappetizing, unrealistic, unnatural, unusual“
    """
    input_prompt = mission + pt
    p = Prompt(input_prompt)
    #将任务描述输入给模型进行优化
    comp = Completion(model="ERNIE-3.5-8K")
    r = comp.do(prompt=p.render()[0])
    output = r['result']
    print(output)
    return output

#文生图函数, 输入为字符串
def t2i(pt):
    i = Text2Image()
    #将prompt输入SD-XL
    resp = i.do(prompt=pt, with_decode="base64",request_timeout=120)
    img_data = resp["body"]["data"][0]["image"]
    #展示SD-XL返回的图片
    img = Image.open(io.BytesIO(img_data))
    img.show()

#测试专用文生图-保存函数，输入中rawdata为prompt列表，save_dir为保存路径
def generate_and_save(rawdata, save_dir):
    count = 0
    for pt in rawdata:
        #print(count)
        t2i = qianfan.Text2Image()
        resp = t2i.do(prompt=pt, with_decode="base64",request_timeout=120)
        img_data = resp["body"]["data"][0]["image"]

        img = Image.open(io.BytesIO(img_data))
        #display(img)

        # 设置保存路径
        save_path = os.path.join(save_dir, f"{count}.png")

        # 确保保存目录存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 保存图片，图片的命名按照数字编号，以保证与prompt顺序对应
        img.save(save_path)
        print(f"Image {count} saved as {save_path}")

        count += 1

