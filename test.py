from qianfan.components import hub
from qianfan.components import Prompt, hub

p = Prompt(name="穿搭灵感")
s = hub.save(p)
new_p = hub.load(json_str=s)
