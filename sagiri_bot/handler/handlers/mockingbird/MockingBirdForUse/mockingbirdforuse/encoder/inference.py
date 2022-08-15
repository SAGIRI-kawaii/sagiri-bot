import torch
import numpy as np
from pathlib import Path

from . import audio
from .model import SpeakerEncoder
from .audio import preprocess_wav  # We want to expose this function from here
from .hparams import hparams as hp
from loguru import logger


class Encoder:
    def __init__(self, model_path: Path):
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = SpeakerEncoder(self._device, torch.device("cpu"))
        checkpoint = torch.load(model_path, self._device)
        self._model.load_state_dict(checkpoint["model_state"])
        self._model.eval()
        logger.info(
            f"Loaded encoder {model_path.name} trained to step {checkpoint['step']}"
        )

    def embed_frames_batch(self, frames_batch):
        """
        Computes embeddings for a batch of mel spectrogram.

        :param frames_batch: a batch mel of spectrogram as a numpy array of float32 of shape
        (batch_size, n_frames, n_channels)
        :return: the embeddings as a numpy array of float32 of shape (batch_size, model_embedding_size)
        """

        frames = torch.from_numpy(frames_batch).to(self._device)
        embed = self._model.forward(frames).detach().cpu().numpy()
        return embed

    def compute_partial_slices(
        self,
        n_samples,
        partial_utterance_n_frames=hp.partials_n_frames,
        min_pad_coverage=0.75,
        overlap=0.5,
        rate=None,
    ):
        """
        Computes where to split an utterance waveform and its corresponding mel spectrogram to obtain
        partial utterances of <partial_utterance_n_frames> each. Both the waveform and the mel
        spectrogram slices are returned, so as to make each partial utterance waveform correspond to
        its spectrogram. This function assumes that the mel spectrogram parameters used are those
        defined in params_data.py.

        The returned ranges may be indexing further than the length of the waveform. It is
        recommended that you pad the waveform with zeros up to wave_slices[-1].stop.

        :param n_samples: the number of samples in the waveform
        :param partial_utterance_n_frames: the number of mel spectrogram frames in each partial
        utterance
        :param min_pad_coverage: when reaching the last partial utterance, it may or may not have
        enough frames. If at least <min_pad_coverage> of <partial_utterance_n_frames> are present,
        then the last partial utterance will be considered, as if we padded the audio. Otherwise,
        it will be discarded, as if we trimmed the audio. If there aren't enough frames for 1 partial
        utterance, this parameter is ignored so that the function always returns at least 1 slice.
        :param overlap: by how much the partial utterance should overlap. If set to 0, the partial
        utterances are entirely disjoint.
        :return: the waveform slices and mel spectrogram slices as lists of array slices. Index
        respectively the waveform and the mel spectrogram with these slices to obtain the partial
        utterances.
        """
        assert 0 <= overlap < 1
        assert 0 < min_pad_coverage <= 1

        if rate != None:
            samples_per_frame = int((hp.sampling_rate * hp.mel_window_step / 1000))
            n_frames = int(np.ceil((n_samples + 1) / samples_per_frame))
            frame_step = int(np.round((hp.sampling_rate / rate) / samples_per_frame))
        else:
            samples_per_frame = int((hp.sampling_rate * hp.mel_window_step / 1000))
            n_frames = int(np.ceil((n_samples + 1) / samples_per_frame))
            frame_step = max(
                int(np.round(partial_utterance_n_frames * (1 - overlap))), 1
            )

        assert 0 < frame_step, "The rate is too high"
        assert (
            frame_step <= hp.partials_n_frames
        ), "The rate is too low, it should be %f at least" % (
            hp.sampling_rate / (samples_per_frame * hp.partials_n_frames)
        )

        # Compute the slices
        wav_slices, mel_slices = [], []
        steps = max(1, n_frames - partial_utterance_n_frames + frame_step + 1)
        for i in range(0, steps, frame_step):
            mel_range = np.array([i, i + partial_utterance_n_frames])
            wav_range = mel_range * samples_per_frame
            mel_slices.append(slice(*mel_range))
            wav_slices.append(slice(*wav_range))

        # Evaluate whether extra padding is warranted or not
        last_wav_range = wav_slices[-1]
        coverage = (n_samples - last_wav_range.start) / (
            last_wav_range.stop - last_wav_range.start
        )
        if coverage < min_pad_coverage and len(mel_slices) > 1:
            mel_slices = mel_slices[:-1]
            wav_slices = wav_slices[:-1]

        return wav_slices, mel_slices

    def embed_utterance(
        self, wav, using_partials: bool = True, return_partials: bool = False, **kwargs
    ):
        """
        Computes an embedding for a single utterance.

        :param wav: a preprocessed (see audio.py) utterance waveform as a numpy array of float32
        :param using_partials: if True, then the utterance is split in partial utterances of
        <partial_utterance_n_frames> frames and the utterance embedding is computed from their
        normalized average. If False, the utterance is instead computed from feeding the entire
        spectogram to the network.
        :param return_partials: if True, the partial embeddings will also be returned along with the
        wav slices that correspond to the partial embeddings.
        :param kwargs: additional arguments to compute_partial_splits()
        :return: the embedding as a numpy array of float32 of shape (model_embedding_size,). If
        <return_partials> is True, the partial utterances as a numpy array of float32 of shape
        (n_partials, model_embedding_size) and the wav partials as a list of slices will also be
        returned. If <using_partials> is simultaneously set to False, both these values will be None
        instead.
        """
        # Process the entire utterance if not using partials
        if not using_partials:
            frames = audio.wav_to_mel_spectrogram(wav)
            embed = self.embed_frames_batch(frames[None, ...])[0]
            if return_partials:
                return embed, None, None
            return embed

        # Compute where to split the utterance into partials and pad if necessary
        wave_slices, mel_slices = self.compute_partial_slices(len(wav), **kwargs)
        max_wave_length = wave_slices[-1].stop
        if max_wave_length >= len(wav):
            wav = np.pad(wav, (0, max_wave_length - len(wav)), "constant")

        # Split the utterance into partials
        frames = audio.wav_to_mel_spectrogram(wav)
        frames_batch = np.array([frames[s] for s in mel_slices])
        partial_embeds = self.embed_frames_batch(frames_batch)

        # Compute the utterance embedding from the partial embeddings
        raw_embed = np.mean(partial_embeds, axis=0)
        embed = raw_embed / np.linalg.norm(raw_embed, 2)

        if return_partials:
            return embed, partial_embeds, wave_slices
        return embed
