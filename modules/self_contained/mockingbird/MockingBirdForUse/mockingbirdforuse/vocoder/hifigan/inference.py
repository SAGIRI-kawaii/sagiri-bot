import torch
from pathlib import Path

from .hparams import hparams as hp
from .models import Generator
from loguru import logger


class HifiGanVocoder:
    def __init__(self, model_path: Path):
        torch.manual_seed(hp.seed)
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.generator = Generator(hp).to(self._device)

        logger.debug("Loading '{}'".format(model_path))
        state_dict_g = torch.load(model_path, map_location=self._device)
        logger.debug("Complete.")

        self.generator.load_state_dict(state_dict_g["generator"])
        self.generator.eval()
        self.generator.remove_weight_norm()

    def infer_waveform(self, mel):
        mel = torch.FloatTensor(mel).to(self._device)
        mel = mel.unsqueeze(0)

        with torch.no_grad():
            y_g_hat = self.generator(mel)
            audio = y_g_hat.squeeze()
        audio = audio.cpu().numpy()

        return audio, hp.sampling_rate
