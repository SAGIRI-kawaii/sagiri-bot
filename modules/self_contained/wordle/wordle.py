from io import BytesIO
from pathlib import Path
from itertools import product
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

word_path = Path(__file__).parent / "words"

all_word = {w.upper() for w in (word_path / "words.txt").read_text(encoding="UTF-8").splitlines()}

word_dic = [p.stem for p in word_path.iterdir() if p.suffix == ".json"]

font = ImageFont.truetype(r"resources/fonts/KarnakPro-Bold.ttf", 20)


class Wordle:
    def __init__(self, word: str):
        self.length = len(word)
        self.word = word
        self.word_upper = word.upper()
        self.finish = False

        self.row = self.length + 1
        self.pointer = 0

        # color
        self.background_color = (255, 255, 255)
        self.none_color = (123, 123, 124)
        self.right_color = (134, 163, 115)
        self.wplace_color = (198, 182, 109)

        # size
        self.padding = 20
        self.block_padding = 10
        self.block_border = 2
        self.block_a = 40

        # font
        self.font_size = 20
        self.font = font

        # Right word
        self.guess_right_chars = set()
        self.history_words = []

        # init wordle_pic
        board_side_width = (
            2 * self.padding
            + (self.length - 1) * self.block_padding
            + self.length * self.block_a
        )
        board_side_height = (
            2 * self.padding
            + self.length * self.block_padding
            + (self.row) * self.block_a
        )
        self.size = (board_side_width, board_side_height)
        self.pic = Image.new("RGB", self.size, self.background_color)
        self.draw = ImageDraw.Draw(self.pic)
        for x, y in product(range(self.length), range(self.length + 1)):
            x_pics = self.padding + (x * (self.block_a + self.block_padding))
            y_pics = self.padding + (y * (self.block_a + self.block_padding))
            self.draw.rectangle(
                (x_pics, y_pics, x_pics + self.block_a, y_pics + self.block_a),
                outline=self.none_color,
                width=self.block_border,
            )

    def get_img(self) -> bytes:
        self.pic.save(b := BytesIO(), format="png")
        return b.getvalue()

    def get_color(self, word: str):
        ret_data = []
        for i in range(self.length):
            c = word[i]
            if c == self.word_upper[i]:
                ret_data.append(self.right_color)
                self.guess_right_chars.add(c)
            elif c in self.word_upper:
                ret_data.append(self.wplace_color)
                self.guess_right_chars.add(c)
            else:
                ret_data.append(self.none_color)
        return ret_data

    def get_hint(self) -> bytes:
        size = (
            (
                2 * self.padding
                + (self.length - 1) * self.block_padding
                + self.length * self.block_a
            ),
            2 * self.padding + self.block_a,
        )

        pic = Image.new("RGB", size, self.background_color)
        draw = ImageDraw.Draw(pic)

        y = self.padding
        char_y = int(y + (self.block_a - self.font_size) / 2)

        for i, l in enumerate(self.word_upper):
            x = self.padding + (i * (self.block_a + self.block_padding))
            draw.rectangle(
                (x, y, x + self.block_a, y + self.block_a),
                fill=self.right_color if l in self.guess_right_chars else None,
                outline=self.none_color,
                width=self.block_border,
            )
            if l in self.guess_right_chars:
                char_x = self.font.getlength(l.upper())
                draw.text(
                    (int(x + (self.block_a - char_x) / 2), char_y),
                    l,
                    self.background_color,
                    self.font,
                )

        pic.save(b := BytesIO(), format="PNG")
        return b.getvalue()

    def guess(self, answer: str) -> Tuple[bool, bool]:
        answer = answer.upper()
        self.history_words.append(answer)
        color = self.get_color(answer)
        y = (
            self.padding
            + (self.pointer * (self.block_a + self.block_padding))
            + self.block_border
        )
        a = self.block_a - 2 * self.block_border
        for n, (l, c) in enumerate(zip(answer, color)):
            x = (
                self.padding
                + (n * (self.block_a + self.block_padding))
                + self.block_border
            )
            self.draw.rectangle((x, y, x + a, y + a), fill=c)
            char_x = self.font.getlength(l)
            self.draw.text(
                (int(x + (a - char_x) / 2), int(y + (a - self.font_size) / 2)),
                l,
                self.background_color,
                self.font,
            )
        self.pointer += 1

        game_end = self.finish = self.pointer >= self.row
        game_win = answer == self.word_upper

        return game_end, game_win
