from io import BytesIO
from .pool_data import POOL
from PIL import Image as IMG

import os
import math
import random
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image

FILE_PATH = os.path.dirname(__file__)
ICON_PATH = os.path.join(FILE_PATH, 'icon')

DEFAULT_POOL = "常驻"  # 默认卡池


class Gacha(object):

    def __init__(self, _pool=DEFAULT_POOL):
        # 实例化的时候就要传进来字符串表明要抽哪个卡池
        self.pool = _pool

        self.last_time_5 = ""  # 记录上一次抽卡的5星是什么
        self.last_time_4 = ""  # 记录上一次抽卡的4星是什么

        # 保底计数,注意这个计数是从0开始的，每一次抽卡（包括第一次）之前都得+1
        self.distance_5_star = 0
        self.distance_4_star = 0

        # 需要生成图片的抽卡结果列表
        self.gacha_list = []

        # 记录多少抽第一次出现UP
        self.last_4_up = 0
        self.last_5_up = 0

        # 记录多少抽第一次出现4星或5星
        self.last_4 = 0
        self.last_5 = 0

        self.gacha_rarity_statistics = {
            # 这个列表记录的是本轮抽卡，每种稀有度各抽到了多少
            '3星': 0,
            '4星': 0,
            '5星': 0
        }

        # 当前是多少抽
        self.current_times = 0

        # 记录抽卡每个角色或装备各抽到多少
        self.gacha_all_statistics = {}

        self.up_probability = self.get_up_probability()
        self._5_star_basic_probability = self.get_5_star_basic_probability()
        self._4_star_basic_probability = self.get_4_star_basic_probability()
        self.distance_frequency = self.get_distance_frequency()

    @staticmethod
    def get_png_path(name):
        # 获取png文件路径，传入的参数是角色或武器名字，会自动在角色和武器文件夹搜索，找不到使用默认图标

        role_name_path = os.path.join(ICON_PATH, "角色图鉴", str(name) + ".png")
        arms_name_path = os.path.join(ICON_PATH, "武器图鉴", str(name) + ".png")

        if os.path.exists(role_name_path):
            return role_name_path

        if os.path.exists(arms_name_path):
            return arms_name_path

        return os.path.join(ICON_PATH, "default.png")

    def is_up(self, name):
        # 检查角色是否在UP里
        # 如果name是一个空字符串表示是第一次抽到4星或5星
        if name == "":
            return True
        if self.pool == "常驻":
            return False

        if (name in POOL[self.pool]['5_star_UP']) or (name in POOL[self.pool]['4_star_UP']):
            return True

        return False

    def is_star(self, name):
        # 检查角色或物品是几星的
        # 返回对应的星星数
        if (name in POOL[self.pool]['5_star_UP']) or (name in POOL[self.pool]['5_star_not_UP']):
            return "★★★★★"
        if (name in POOL[self.pool]['4_star_UP']) or (name in POOL[self.pool]['4_star_not_UP']):  # 4星常驻池就包含所有4星角色装备了
            return "★★★★"
        return "★★★"

    @staticmethod
    def pic2bytes(im) -> bytes:
        # im是Image对象，把Image图片转成base64
        bio = BytesIO()
        im.save(bio, format='PNG')
        return bio.getvalue()

    def concat_pic(self, border=5):
        # self.gacha_list是一个列表，这个函数找到列表中名字对应的图片，然后拼接成一张大图返回
        num = len(self.gacha_list)
        w, h = [130, 160]

        des = IMG.new('RGBA', (w * min(num, border), h * math.ceil(num / border)), (255, 255, 255, 0))

        for i in range(num):
            im = IMG.open(self.get_png_path(self.gacha_list[i]))
            im = im.resize((130, 160))

            w_row = (i % border) + 1
            h_row = math.ceil((i + 1) / border)

            pixel_w = (w_row - 1) * w
            pixel_h = (h_row - 1) * h

            des.paste(im, (int(pixel_w), int(pixel_h)))

        return des

    def add_gacha_all_statistics(self, name):
        # 把每一次抽卡结果添加到gacha_all_statistics
        if name in self.gacha_all_statistics.keys():
            self.gacha_all_statistics[name] += 1
        else:
            self.gacha_all_statistics[name] = 1

    def update_last(self, name):
        # 这个方法用来更新第一次抽到4星或5星或UP的计数
        if not self.last_4_up and name in POOL[self.pool]['4_star_UP']:
            self.last_4_up = self.current_times + 1

        if not self.last_5_up and name in POOL[self.pool]['5_star_UP']:
            self.last_5_up = self.current_times + 1

        if not self.last_4 and (
            (name in POOL[self.pool]['4_star_not_UP'])
            or (name in POOL[self.pool]['4_star_UP'])
        ):
            self.last_4 = self.current_times + 1

        if not self.last_5 and (
            (name in POOL[self.pool]['5_star_not_UP'])
            or (name in POOL[self.pool]['5_star_UP'])
        ):
            self.last_5 = self.current_times + 1

    def is_guaranteed(self, frequency):
        # 检查本轮抽卡是不是全保底
        if frequency == 180:
            if self.gacha_rarity_statistics['5星'] == 2 and self.gacha_rarity_statistics['4星'] == 16:
                return True
        elif frequency == 90:
            if self.gacha_rarity_statistics['5星'] == 1 and self.gacha_rarity_statistics['4星'] == 8:
                return True
        return False

    def get_most_arms(self):
        # 返回抽出的武器抽出最多的是哪个，抽出了多少次
        if not self.gacha_all_statistics:
            raise KeyError("字典 self.gacha_all_statistics 是空的")
        most_value = max(self.gacha_all_statistics.values())
        for key, value in self.gacha_all_statistics.items():
            if most_value == value:
                return {"name": key, "most": value}

    def get_up_probability(self):
        # 获取上一次抽卡抽到5星 UP 时，再次获取5星概率是多少
        if self.pool.count("武器"):
            return 0.75
        return 0.5

    def get_5_star_basic_probability(self):
        # 获取5星的基础概率
        if self.pool.count("武器"):
            return 0.007
        return 0.006

    def get_4_star_basic_probability(self):
        # 获取4星的基础概率
        if self.pool.count("武器"):
            return 0.060
        return 0.051

    def get_distance_frequency(self):
        # 获取当前卡池的保底抽卡次数
        if self.pool.count("武器"):
            return 80
        return 90

    def get_5_star(self):
        # 先检查上次5星是否是UP，不是UP本次抽取必定是 UP，
        # 如果上次是UP，角色UP池本次有50%的概率还是 UP，50%概率非 UP，
        # 武器UP池本次有75%的概率还是 UP，25%概率非 UP，详情看UP_PROBABILITY

        # 先看是不是常驻池
        if self.pool == '常驻':
            return random.choice(POOL[self.pool]['5_star_not_UP'])

        # 下边是角色或武器的UP
        if self.is_up(self.last_time_5):

            if random.random() < self.up_probability:
                return random.choice(POOL[self.pool]['5_star_UP'])
            else:
                return random.choice(POOL[self.pool]['5_star_not_UP'])
        else:
            return random.choice(POOL[self.pool]['5_star_UP'])

    def get_4_star(self):
        # 先检查上次4星是否是UP，不是UP本次抽取必定是 UP，
        # 如果上次是UP，角色UP池本次有50%的概率还是 UP，50%概率非 UP
        # 武器UP池本次有75%的概率还是UP，25%概率非 UP，详情看UP_PROBABILITY

        # 先看是不是常驻池
        if self.pool == '常驻':
            return random.choice(POOL[self.pool]['4_star_not_UP'])

        # 下边是角色或武器的UP
        if self.is_up(self.last_time_4):
            if random.random() < self.up_probability:
                return random.choice(POOL[self.pool]['4_star_UP'])
            else:
                return random.choice(POOL[self.pool]['4_star_not_UP'])
        else:
            return random.choice(POOL[self.pool]['4_star_UP'])

    def get_5_star_probability(self):
        # 获取本次抽5星的概率是多少

        if self.pool.count("武器"):
            # 这是武器up池5星概率
            if self.distance_5_star <= 62:
                return self._5_star_basic_probability
            else:
                return self._5_star_basic_probability + 0.056 * (self.distance_5_star - 62)
        else:
            # 下边是常驻池和角色UP池
            # 这两个保底和概率是相同的所以放在一起
            if self.distance_5_star <= 73:
                return self._5_star_basic_probability
            else:
                return self._5_star_basic_probability + 0.06 * (self.distance_5_star - 73)

    def gacha_one(self):
        # self.last_time_4表示上一个4星角色
        # self.last_time_5表示上一个5星角色
        # self.distance_4_star是4星保底计数
        # self.distance_5_star是5星保底计数
        self.distance_4_star += 1
        self.distance_5_star += 1

        _5_star_probability = self.get_5_star_probability()

        r = random.random()

        # 先检查是不是保底5星
        if self.distance_5_star % self.distance_frequency == 0:
            self.gacha_rarity_statistics["5星"] += 1
            self.distance_5_star = 0  # 重置保底计数
            self.last_time_5 = self.get_5_star()  # 抽一次卡，把结果赋值留给下一次抽卡判断
            return self.last_time_5  # 返回刚抽出的卡

        # 检查是不是概率5星
        if r < _5_star_probability:
            self.gacha_rarity_statistics["5星"] += 1
            self.distance_5_star = 0
            self.last_time_5 = self.get_5_star()  # 抽一次卡，把结果赋值留给下一次抽卡判断
            return self.last_time_5  # 返回刚抽出的卡

        # 检查是不是保底4星
        if self.distance_4_star % 10 == 0:
            self.gacha_rarity_statistics["4星"] += 1
            self.distance_4_star = 0
            self.last_time_4 = self.get_4_star()
            return self.last_time_4

        # 检查是不是概率4星
        # 由于是先判断5星的概率出货，所以4星的实际概率是4星原概率加上5星的概率
        if r < (self._5_star_basic_probability + self._4_star_basic_probability):
            self.gacha_rarity_statistics["4星"] += 1
            self.distance_4_star = 0
            self.last_time_4 = self.get_4_star()
            return self.last_time_4

        # 以上都不是返回3星
        self.gacha_rarity_statistics["3星"] += 1
        return random.choice(POOL[self.pool]['3_star_not_UP'])

    def gacha_10(self) -> MessageChain:
        # 抽10连
        if not (self.pool in POOL.keys()):
            return MessageChain('当前卡池已结束，请使用 原神卡池切换 切换其他卡池')

        gacha_txt = ""

        for self.current_times in range(10):

            new_gacha = self.gacha_one()
            self.gacha_list.append(new_gacha)
            gacha_txt += new_gacha
            gacha_txt += self.is_star(new_gacha)

            if (self.current_times + 1) % 5 == 0:
                gacha_txt += '\n'

            self.add_gacha_all_statistics(new_gacha)  # 把所有抽卡结果添加到gacha_all_statistics用于最后统计

            self.update_last(new_gacha)  # 更新第一次抽到的计数

        mes = [
            Plain(text='本次祈愿得到以下角色装备：\n'),
            Image(data_bytes=self.pic2bytes(self.concat_pic())),
            Plain(text=f'\n{gacha_txt}')
        ]

        if self.last_4:  # 如果self.last_4为0表示没有抽到，这句话就不写了，下边3个判断标准一样
            mes.append(Plain(text=f'第 {self.last_4} 抽首次出现4★!\n'))
        if self.last_4_up:
            mes.append(Plain(text=f'第 {self.last_4_up} 抽首次出现4★UP!\n'))
        if self.last_5:
            mes.append(Plain(text=f'第 {self.last_5} 抽首次出现5★!\n'))
        if self.last_5_up:
            mes.append(Plain(text=f'第 {self.last_5_up} 抽首次出现5★UP!\n'))

        mes.append(Plain(text=f"\n* 本次抽取卡池为 {self.pool} \n* 发送 原神卡池切换 可切换卡池"))

        return MessageChain(mes)

    def gacha_90(self, frequency=90) -> MessageChain:
        # 抽一井
        if not (self.pool in POOL.keys()):
            return MessageChain('当前卡池已结束，请使用 原神卡池切换 切换其他卡池')

        gacha_txt = ""

        for self.current_times in range(frequency):

            new_gacha = self.gacha_one()

            if not (new_gacha in POOL[self.pool]['3_star_not_UP']):  # 抽一井时图片上不保留3星的武器
                self.gacha_list.append(new_gacha)

            self.add_gacha_all_statistics(new_gacha)  # 把所有抽卡结果添加到gacha_all_statistics用于最后统计

            self.update_last(new_gacha)  # 更新第一次抽到的计数

        gacha_txt += f"★★★★★×{self.gacha_rarity_statistics['5星']}    ★★★★×{self.gacha_rarity_statistics['4星']}    ★★★×{self.gacha_rarity_statistics['3星']}\n"

        mes = [
            Plain(text='本次祈愿得到以下角色装备：\n'),
            Image(data_bytes=self.pic2bytes(self.concat_pic())),
            Plain(text=f'\n{gacha_txt}')
        ]

        if self.last_4:  # 如果self.last_4为0表示没有抽到，这句话就不写了，下边3个判断标准一样
            mes.append(Plain(text=f'第 {self.last_4} 抽首次出现4★!\n'))
        if self.last_4_up:
            mes.append(Plain(text=f'第 {self.last_4_up} 抽首次出现4★UP!\n'))
        if self.last_5:
            mes.append(Plain(text=f'第 {self.last_5} 抽首次出现5★!\n'))
        if self.last_5_up:
            mes.append(Plain(text=f'第 {self.last_5_up} 抽首次出现5★UP!\n'))

        most_arms = self.get_most_arms()
        mes.append(Plain(text=f"本次抽取最多的装备是 {most_arms['name']} {self.is_star(most_arms['name'])} ,共抽取到 {most_arms['most']} 次\n"))

        if self.is_guaranteed(frequency):
            mes.append(Plain(text="居然全是保底，你脸也太黑了\n"))

        mes.append(Plain(text=f"\n* 本次抽取卡池为 {self.pool} \n* 发送 原神卡池切换 可切换卡池"))
        return MessageChain(mes)


def gacha_info(pool=DEFAULT_POOL) -> MessageChain:
    # UP角色信息
    info_txt = f'当前卡池为 {pool} ，UP信息如下：\n'
    up_info = []

    for _5_star in POOL[pool]['5_star_UP']:
        im = IMG.open(Gacha.get_png_path(_5_star))
        im = Gacha.pic2bytes(im)
        up_info.append(Image(data_bytes=im))
        up_info.append(Plain(text=f"\n{_5_star} ★★★★★"))

    for _4_star in POOL[pool]['4_star_UP']:
        im = IMG.open(Gacha.get_png_path(_4_star))
        im = Gacha.pic2bytes(im)
        up_info.append(Image(data_bytes=im))
        up_info.append(Plain(text=f"\n{_4_star} ★★★★"))

    if not up_info:
        # 如果up_info是空的，表示当前是常驻池没有UP
        up_info.append(Plain(text="常驻池没有UP"))

    return MessageChain([Plain(text=info_txt)] + up_info)
