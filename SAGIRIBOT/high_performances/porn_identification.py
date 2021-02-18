from third_party_library.nsfw_detector import nsfw_detector_predictor

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain

model = nsfw_detector_predictor.load_model('./third_party_library/nsfw_detector/nsfw_mobilenet2.224x224.h5')


async def porn_identification(path: str) -> list:
    result = nsfw_detector_predictor.classify(model, path)
    max_label = None
    max_percent = 0
    result = result[path]
    for key in result.keys():
        max_label = key if result[key] > max_percent else max_label
        max_percent = result[key] if result[key] > max_percent else max_percent
    # print(max_label, max_percent)
    return [
        "quoteSource",
        MessageChain.create([
            Plain(text=f"图片评级：{max_label}\n准确度：{round(max_percent * 100, 2)}%"),
            Plain(text=f"全部结果：{result}")
        ])
    ]
