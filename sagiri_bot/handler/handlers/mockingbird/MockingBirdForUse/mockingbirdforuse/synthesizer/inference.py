import torch
import librosa
import numpy as np
from pathlib import Path
from typing import Union, List
from pypinyin import lazy_pinyin, Style

from .hparams import hparams as hp
from .utils.symbols import symbols
from .models.tacotron import Tacotron
from .utils.text import text_to_sequence
from .utils.logmmse import denoise, profile_noise
from loguru import logger


class Synthesizer:
    def __init__(self, model_path: Path):
        # Check for GPU
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        logger.info(f"Synthesizer using device: {self.device}")

        self._model = Tacotron(
            embed_dims=hp.tts_embed_dims,
            num_chars=len(symbols),
            encoder_dims=hp.tts_encoder_dims,
            decoder_dims=hp.tts_decoder_dims,
            n_mels=hp.num_mels,
            fft_bins=hp.num_mels,
            postnet_dims=hp.tts_postnet_dims,
            encoder_K=hp.tts_encoder_K,
            lstm_dims=hp.tts_lstm_dims,
            postnet_K=hp.tts_postnet_K,
            num_highways=hp.tts_num_highways,
            dropout=hp.tts_dropout,
            stop_threshold=hp.tts_stop_threshold,
            speaker_embedding_size=hp.speaker_embedding_size,
        ).to(self.device)

        self._model.load(model_path, self.device)
        self._model.eval()

        logger.info(
            'Loaded synthesizer "%s" trained to step %d'
            % (model_path.name, self._model.state_dict()["step"])
        )

    def synthesize_spectrograms(
        self,
        texts: List[str],
        embeddings: Union[np.ndarray, List[np.ndarray]],
        return_alignments=False,
        style_idx=0,
        min_stop_token=5,
        steps=2000,
    ):
        """
        Synthesizes mel spectrograms from texts and speaker embeddings.

        :param texts: a list of N text prompts to be synthesized
        :param embeddings: a numpy array or list of speaker embeddings of shape (N, 256)
        :param return_alignments: if True, a matrix representing the alignments between the
        characters
        and each decoder output step will be returned for each spectrogram
        :return: a list of N melspectrograms as numpy arrays of shape (80, Mi), where Mi is the
        sequence length of spectrogram i, and possibly the alignments.
        """

        print("Read " + str(texts))
        texts = [
            " ".join(lazy_pinyin(v, style=Style.TONE3, neutral_tone_with_five=True))
            for v in texts
        ]
        print("Synthesizing " + str(texts))
        # Preprocess text inputs
        inputs = [text_to_sequence(text, hp.tts_cleaner_names) for text in texts]
        if not isinstance(embeddings, list):
            embeddings = [embeddings]

        # Batch inputs
        batched_inputs = [
            inputs[i : i + hp.synthesis_batch_size]
            for i in range(0, len(inputs), hp.synthesis_batch_size)
        ]
        batched_embeds = [
            embeddings[i : i + hp.synthesis_batch_size]
            for i in range(0, len(embeddings), hp.synthesis_batch_size)
        ]

        specs = []
        alignments = []
        for i, batch in enumerate(batched_inputs, 1):
            print(f"Generating {i}/{len(batched_inputs)}")

            # Pad texts so they are all the same length
            text_lens = [len(text) for text in batch]
            max_text_len = max(text_lens)
            chars = [pad1d(text, max_text_len) for text in batch]
            chars = np.stack(chars)

            # Stack speaker embeddings into 2D array for batch processing
            speaker_embeds = np.stack(batched_embeds[i - 1])

            # Convert to tensor
            chars = torch.tensor(chars).long().to(self.device)
            speaker_embeddings = torch.tensor(speaker_embeds).float().to(self.device)

            # Inference
            _, mels, alignments = self._model.generate(
                chars,
                speaker_embeddings,
                style_idx=style_idx,
                min_stop_token=min_stop_token,
                steps=steps,
            )
            mels = mels.detach().cpu().numpy()
            for m in mels:
                # Trim silence from end of each spectrogram
                while np.max(m[:, -1]) < hp.tts_stop_threshold:
                    m = m[:, :-1]
                specs.append(m)

        print("Done.")
        return (specs, alignments) if return_alignments else specs

    @staticmethod
    def load_preprocess_wav(fpath):
        """
        Loads and preprocesses an audio file under the same conditions the audio files were used to
        train the synthesizer.
        """
        wav = librosa.load(path=str(fpath), sr=hp.sample_rate)[0]
        if hp.rescale:
            wav = wav / np.abs(wav).max() * hp.rescaling_max
        # denoise
        if len(wav) > hp.sample_rate * (0.3 + 0.1):
            noise_wav = np.concatenate(
                [
                    wav[: int(hp.sample_rate * 0.15)],
                    wav[-int(hp.sample_rate * 0.15) :],
                ]
            )
            profile = profile_noise(noise_wav, hp.sample_rate)
            wav = denoise(wav, profile)
        return wav


def pad1d(x, max_len, pad_value=0):
    return np.pad(x, (0, max_len - len(x)), mode="constant", constant_values=pad_value)
