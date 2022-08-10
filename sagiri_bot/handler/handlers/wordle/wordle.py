import os
import json
import random
import PIL.Image
from io import BytesIO
from pathlib import Path
from asyncio import Lock
from PIL import ImageFont, ImageDraw
from typing import Tuple, List, Union, Optional


class Wordle(object):

    length: int  # 单词长度

    size: Tuple[int, int]  # 画板尺寸

    board: PIL.Image.Image  # 画板

    word: str  # 单词

    dic: str  # 字典

    row: int  # 可猜次数

    current_row: int  # 目前行数

    padding: int  # 边界长度

    block_side_length: int  # 文字块边长

    white_side_length: int  # 文字块内部白色范围边长

    block_padding: int  # 文字块间距

    block_border: int  # 块边框宽度

    font: ImageFont.FreeTypeFont  # 字体

    font_size: int  # 字体大小

    wrong_place: Union[str, Tuple[int, int, int]]  # 错误位置颜色

    correct_place: Union[str, Tuple[int, int, int]]  # 正确位置颜色

    none_chara: Union[str, Tuple[int, int, int]]  # 错误字母颜色

    border_color: Union[str, Tuple[int, int, int]]  # 边界颜色

    block_color: Union[str, Tuple[int, int, int]]  # 文字块颜色

    font_color: Union[str, Tuple[int, int, int]]  # 文字颜色

    hint_set: set  # 记录提示信息

    guess_word: List[str]  # 记录已猜单词

    draw_mutex: Lock  # 绘图信号量

    game_end: bool = False  # 一局游戏是否结束

    def __init__(
        self,
        length: int,
        word: Optional[str] = None,
        dic: str = "CET4",
        padding: int = 20,
        block_side_length: int = 40,
        block_padding: int = 10,
        block_border: int = 2,
        font_size: int = 20,
        wrong_place: Union[str, Tuple[int, int, int]] = (198, 182, 109),
        correct_place: Union[str, Tuple[int, int, int]] = (134, 163, 115),
        none_chara: Union[str, Tuple[int, int, int]] = (123, 123, 124),
        border_color: Union[str, Tuple[int, int, int]] = (123, 123, 124),
        font_color: Union[str, Tuple[int, int, int]] = (255, 255, 255),
    ):
        self.dic = dic
        if word:
            self.length = len(word)
            self.word = word
        else:
            self.length = length
            self.word = self.random_word()
        self.padding = padding
        self.block_side_length = block_side_length
        self.block_padding = block_padding
        self.block_border = block_border
        self.font_size = font_size
        self.font = ImageFont.truetype(
            str(Path(os.getcwd()) / "statics" / "fonts" / "KarnakPro-Bold.ttf"),
            font_size,
        )
        self.wrong_place = wrong_place
        self.correct_place = correct_place
        self.none_chara = none_chara
        self.border_color = border_color
        self.font_color = font_color
        self.hint_set = set()
        self.guess_word = []
        self.draw_mutex = Lock()
        self.game_end = False
        self.row = self.get_retry_times(self.length)
        board_side_width = (
            2 * padding
            + (self.length - 1) * block_padding
            + self.length * block_side_length
        )
        board_side_height = (
            2 * padding + (self.row - 1) * block_padding + self.row * block_side_length
        )
        self.size = (board_side_width, board_side_height)
        self.current_row = 0
        self.board = PIL.Image.new("RGB", self.size, "white")
        block = PIL.Image.new(
            "RGB", (block_side_length, block_side_length), border_color
        )
        white_side_length = block_side_length - 2 * block_border
        self.white_side_length = white_side_length
        white = PIL.Image.new("RGB", (white_side_length, white_side_length), "white")
        block.paste(white, (block_border, block_border))
        for i in range(self.length):
            for j in range(self.row):
                self.board.paste(
                    block,
                    (
                        padding + i * (block_side_length + block_padding),
                        padding + j * (block_side_length + block_padding),
                    ),
                )

    def random_word(self) -> str:
        return random.choice(list(word_list[self.dic][self.length].keys()))

    @staticmethod
    def get_retry_times(length: int) -> int:
        return length + 1

    def guess(
        self, word: str
    ) -> Optional[Tuple[bool, bool, bool, bool, PIL.Image.Image]]:

        """game_end: bool, win: bool, legal: bool, duplicate: bool, board: PIL.Image.Image"""

        if self.current_row >= self.row or self.game_end:
            return None
        if not self.legal_word(word):
            return False, False, False, False, self.board
        elif word.lower() in self.guess_word:
            return False, False, True, True, self.board
        else:
            self.guess_word.append(word.lower())
            self.draw(word)
            self.game_end = self.current_row == self.row or self.correct_word(word)
            return (
                self.current_row == self.row or self.correct_word(word),
                self.correct_word(word),
                True,
                False,
                self.board,
            )

    @staticmethod
    def legal_word(word: str) -> bool:
        return (
            root.search(word.lower()) or root.search(word.upper()) or root.search(word)
        )

    def correct_word(self, word: str) -> bool:
        return word.lower() == self.word.lower()

    def draw(self, word: str) -> "Wordle":
        char_color = self.get_color(word.lower())
        x = self.padding
        y = self.padding + self.current_row * (
            self.block_side_length + self.block_padding
        )
        for i in range(self.length):
            char = char_color[i][0].upper()
            color = char_color[i][1]
            block = PIL.Image.new(
                "RGB",
                (self.block_side_length, self.block_side_length),
                self.border_color,
            )
            char_block = PIL.Image.new(
                "RGB", (self.white_side_length, self.white_side_length), color
            )
            canvas = ImageDraw.Draw(char_block)
            font_size = self.font.getsize(char)
            canvas.text(
                (
                    int((self.white_side_length - font_size[0]) / 2),
                    int((self.white_side_length - font_size[1]) / 2),
                ),
                char,
                self.font_color,
                self.font,
            )
            block.paste(char_block, (self.block_border, self.block_border))
            self.board.paste(block, (x, y))
            x += self.block_side_length + self.block_padding
        self.current_row += 1
        return self

    def get_color(self, w: str) -> List[Tuple[str, Tuple[int, int, int]]]:
        result = []
        lower_answer = self.word.lower()
        for i, char in enumerate(w):
            if char == lower_answer[i]:
                self.hint_set.add(char)
                result.append((char, self.correct_place))
            elif char in lower_answer:
                self.hint_set.add(char)
                result.append((char, self.wrong_place))
            else:
                result.append((char, self.none_chara))
        return result

    def get_board_bytes(self) -> bytes:
        bytes_io = BytesIO()
        self.board.save(bytes_io, format="PNG")
        return bytes_io.getvalue()

    def get_hint(self) -> str:
        return "".join(i if i in self.hint_set else "*" for i in self.word)

    def draw_hint(self) -> bytes:
        hint_canvas = PIL.Image.new(
            "RGB",
            (
                2 * self.padding
                + self.block_side_length * self.length
                + self.block_padding * (self.length - 1),
                2 * self.padding + self.block_side_length,
            ),
            "white",
        )
        hint = self.get_hint()
        for i, char in enumerate(hint):
            char = char.upper()
            block = PIL.Image.new(
                "RGB",
                (self.block_side_length, self.block_side_length),
                self.border_color,
            )
            char_block = PIL.Image.new(
                "RGB",
                (self.white_side_length, self.white_side_length),
                self.correct_place if char != "*" else "white",
            )
            canvas = ImageDraw.Draw(char_block)
            font_size = self.font.getsize(char)
            if char != "*":
                canvas.text(
                    (
                        int((self.white_side_length - font_size[0]) / 2),
                        int((self.white_side_length - font_size[1]) / 2),
                    ),
                    char,
                    self.font_color,
                    self.font,
                )
            block.paste(char_block, (self.block_border, self.block_border))
            hint_canvas.paste(
                block,
                (
                    self.padding + i * (self.block_side_length + self.block_padding),
                    self.padding,
                ),
            )
        bytes_io = BytesIO()
        hint_canvas.save(bytes_io, format="PNG")
        return bytes_io.getvalue()


class TrieNode(object):

    nodes: dict

    is_leaf: bool

    def __init__(self):
        self.nodes = {}
        self.is_leaf = False

    def insert(self, word: str):
        curr = self
        for char in word:
            if char not in curr.nodes:
                curr.nodes[char] = TrieNode()
            curr = curr.nodes[char]
        curr.is_leaf = True

    def insert_many(self, *words):
        for word in words:
            self.insert(word)

    def search(self, word: str):
        curr = self
        for char in word:
            if char not in curr.nodes:
                return False
            curr = curr.nodes[char]
        return curr.is_leaf

    def search_lower(self, word: str):
        curr = self
        for char in word:
            if char in curr.nodes:
                curr = curr.nodes[char]
            elif char.upper() not in curr.nodes:
                return False
            else:
                curr = curr.nodes[char.upper()]
        return curr.is_leaf


word_list = {}
word_dics = [
    i[:-5]
    for i in os.listdir(Path(os.path.dirname(__file__)) / "words")
    if i.endswith(".json")
]

for dic in word_dics:
    with open(
        Path(os.path.dirname(__file__)) / "words" / f"{dic}.json", "r", encoding="utf-8"
    ) as r:
        word_list[dic] = {}
        data = json.load(r)
        for word in data.keys():
            if len(word) in word_list[dic]:
                word_list[dic][len(word)][word] = data[word]
            else:
                word_list[dic][len(word)] = {word: data[word]}
root = TrieNode()
for key in word_list:
    for length in word_list[key].keys():
        root.insert_many(*list(word_list[key][length].keys()))

with open(
    Path(os.path.dirname(__file__)) / "words" / "words.txt", "r", encoding="utf-8"
) as r:
    words = r.read().split("\n")
    for word in words:
        root.insert(word.strip())
