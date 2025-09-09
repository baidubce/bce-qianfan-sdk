import qianfan
import os

def bacth_completion():
    chat_client = qianfan.ChatCompletion(version="2",model="deepseek-v3") # deepseek-v3

    task_list = [
        {
            "messages": [{"content": "你好，你是谁", "role": "user"}],
            "system": "你是一个善于助人的医生，请以医生的语气回答问题"
        },
        {
            "messages": [{"content": "你好，你是谁", "role": "user"}],
            "system": "你是一个善于助人的老师,请以老师的语气回答问题"
        }
    ]
    # 批量请求
    results = chat_client.batch_do(body_list=task_list,enable_reading_buffer=True).results()
    print(results)
    for result in results:
        print(result.body)



def bacth_images_generation():
    vision_client = qianfan.Text2Image(version="2",model="irag-1.0")

    prompt_list = [
        "画一只企鹅",
        "画一匹马"
    ]
    # 批量请求
    results = vision_client.batch_do(prompt_list=prompt_list).results()
    print(results)
    for result in results:
        print(result.body)


os.environ["QIANFAN_BEARER_TOKEN"] = ""

bacth_images_generation()

exit(1)