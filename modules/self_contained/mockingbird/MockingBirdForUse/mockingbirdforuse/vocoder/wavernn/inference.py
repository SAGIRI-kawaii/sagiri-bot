import torch
from pathlib import Path

from .hparams import hparams as hp
from .models.fatchord_version import WaveRNN
from loguru import logger


class WaveRNNVocoder:
    def __init__(self, model_path: Path):
        logger.debug("Building Wave-RNN")
        self._model = WaveRNN(
            rnn_dims=hp.voc_rnn_dims,
            fc_dims=hp.voc_fc_dims,
            bits=hp.bits,
            pad=hp.voc_pad,
            upsample_factors=hp.voc_upsample_factors,
            feat_dims=hp.num_mels,
            compute_dims=hp.voc_compute_dims,
            res_out_dims=hp.voc_res_out_dims,
            res_blocks=hp.voc_res_blocks,
            hop_length=hp.hop_length,
            sample_rate=hp.sample_rate,
            mode=hp.voc_mode,
        )

        if torch.cuda.is_available():
            self._model = self._model.cuda()
            self._device = torch.device("cuda")
        else:
            self._device = torch.device("cpu")

        logger.debug("Loading model weights at %s" % model_path)
        checkpoint = torch.load(model_path, self._device)
        self._model.load_state_dict(checkpoint["model_state"])
        self._model.eval()

    def infer_waveform(
        self, mel, normalize=True, batched=True, target=8000, overlap=800
    ):
        """
        Infers the waveform of a mel spectrogram output by the synthesizer (the format must match
        that of the synthesizer!)

        :param normalize:
        :param batched:
        :param target:
        :param overlap:
        :return:
        """

        if normalize:
            mel = mel / hp.mel_max_abs_value
        mel = torch.from_numpy(mel[None, ...])
        wav = self._model.generate(mel, batched, target, overlap, hp.mu_law)
        return wav, hp.sample_rate
