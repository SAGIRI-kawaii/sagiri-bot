from keras.applications.vgg16 import VGG16
from keras.applications.vgg16 import preprocess_input, decode_predictions
from PIL import Image as IMG
from io import BytesIO
import numpy as np
import aiohttp

from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import MessageChain

from SAGIRIBOT.basics.write_log import write_log
from SAGIRIBOT.basics.get_config import get_config
from SAGIRIBOT.data_manage.update_data.set_get_image_ready import set_get_img_ready
from SAGIRIBOT.data_manage.update_data.update_total_calls import update_total_calls
from SAGIRIBOT.data_manage.get_data.get_total_calls import get_total_calls

model = VGG16(weights='imagenet', include_top=True)


async def object_predict_vgg16(group_id: int, member_id: int, img: Image):
    await set_get_img_ready(group_id, member_id, False, "predictReady")
    img_url = img.url

    predict_total_count = await get_total_calls("predict") + 1
    await update_total_calls(predict_total_count, "predict")
    path = "%s%s.png" % (await get_config("predictPath"), predict_total_count)

    async with aiohttp.ClientSession() as session:
        async with session.get(url=img_url) as resp:
            img_content = await resp.read()
    image = IMG.open(BytesIO(img_content))
    image.save(path)

    # Input：要辨識的影像
    # img = image.load_img(img_path, target_size=(224, 224))
    x = np.array(IMG.open(path).resize((224, 224)))
    # x = image.img_to_array(img) #转化为浮点型
    x = np.expand_dims(x, axis=0)  # 转化为张量size为(1, 224, 224, 3)
    x = preprocess_input(x)
    # 預測，取得features，維度為 (1,1000)
    features = model.predict(x)
    # 取得前五個最可能的類別及機率
    pred = decode_predictions(features, top=5)[0]
    # 整理预测结果,value
    values = []
    bar_label = []
    for element in pred:
        values.append(element[2])
        bar_label.append(element[1])
    print(path)
    for i in range(5):
        print(bar_label[i], values[i])
    await write_log("predict", path, member_id, group_id, True, "img")
    msg = [Plain(text="\nPredict Result:")]
    for i in range(5):
        msg.append(Plain(text="\n%s:%2.2f%%" % (bar_label[i], values[i] * 100)))
    return [
        "quoteSource",
        MessageChain.create(msg)
    ]
