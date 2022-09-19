import re
import librosa
import numpy as np
from io import BytesIO
from pathlib import Path
from loguru import logger
from scipy.io import wavfile
from typing import List, Literal, Optional

from .synthesizer.inference import Synthesizer
from .vocoder.hifigan.inference import HifiGanVocoder
from .vocoder.wavernn.inference import WaveRNNVocoder
from .encoder.inference import Encoder, preprocess_wav


def process_text(text: str) -> List[str]:
    punctuation = "！，。、,?!,"  # punctuate and split/clean text
    text = re.sub(f"[{punctuation}]+", "\n", text)
    return [
        processed_text.strip()
        for processed_text in text.split("\n")
        if processed_text
    ]


class MockingBird:
    def __init__(self):
        self.encoder: Optional[Encoder] = None
        self.gan_vocoder: Optional[HifiGanVocoder] = None
        self.rnn_vocoder: Optional[WaveRNNVocoder] = None
        self.synthesizer: Optional[Synthesizer] = None

    def load_model(
        self,
        encoder_path: Path,
        gan_vocoder_path: Optional[Path] = None,
        rnn_vocoder_path: Optional[Path] = None,
    ):
        """
        设置 Encoder模型 和 Vocoder模型 路径

        Args:
            encoder_path (Path): Encoder模型路径
            gan_vocoder_path (Path): HifiGan Vocoder模型路径，可选，需要用到 HifiGan 类型时必须填写
            rnn_vocoder_path (Path): WaveRNN Vocoder模型路径，可选，需要用到 WaveRNN 类型时必须填写
        """
        self.encoder = Encoder(encoder_path)
        if gan_vocoder_path:
            self.gan_vocoder = HifiGanVocoder(gan_vocoder_path)
        if rnn_vocoder_path:
            self.rnn_vocoder = WaveRNNVocoder(rnn_vocoder_path)

    def set_synthesizer(self, synthesizer_path: Path):
        """
        设置Synthesizer模型路径

        Args:
            synthesizer_path (Path): Synthesizer模型路径
        """
        self.synthesizer = Synthesizer(synthesizer_path)
        logger.info(f"using synthesizer model: {synthesizer_path}")

    def synthesize(
        self,
        text: str,
        input_wav: Path,
        vocoder_type: Literal["HifiGan", "WaveRNN"] = "HifiGan",
        style_idx: int = 0,
        min_stop_token: int = 5,
        steps: int = 1000,
    ) -> BytesIO:
        """
        生成语音

        Args:
            text (str): 目标文字
            input_wav (Path): 目标录音路径
            vocoder_type (HifiGan / WaveRNN): Vocoder模型，默认使用HifiGan
            style_idx (int, optional): Style 范围 -1~9，默认为 0
            min_stop_token (int, optional): Accuracy(精度) 范围3~9，默认为 5
            steps (int, optional): MaxLength(最大句长) 范围200~2000，默认为 1000
        """
        if not self.encoder:
            raise Exception("Please set encoder path first")

        if not self.synthesizer:
            raise Exception("Please set synthesizer path first")

        # Load input wav
        wav, sample_rate = librosa.load(input_wav)

        encoder_wav = preprocess_wav(wav, sample_rate)
        embed, _, _ = self.encoder.embed_utterance(encoder_wav, return_partials=True)

        # Load input text
        texts = process_text(text)

        # synthesize and vocode
        embeds = [embed] * len(texts)
        specs = self.synthesizer.synthesize_spectrograms(
            texts,
            embeds,
            style_idx=style_idx,
            min_stop_token=min_stop_token,
            steps=steps,
        )
        spec = np.concatenate(specs, axis=1)
        if vocoder_type == "WaveRNN":
            if not self.rnn_vocoder:
                raise Exception("Please set wavernn vocoder path first")
            wav, sample_rate = self.rnn_vocoder.infer_waveform(spec)
        elif self.gan_vocoder:
            wav, sample_rate = self.gan_vocoder.infer_waveform(spec)

        else:
            raise Exception("Please set hifigan vocoder path first")
        # Return cooked wav
        out = BytesIO()
        wavfile.write(out, sample_rate, wav.astype(np.float32))
        return out
