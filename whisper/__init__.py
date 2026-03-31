import torch
import torchaudio

from .tokenizer import Tokenizer


def log_mel_spectrogram(audio: torch.Tensor, n_mels: int = 80) -> torch.Tensor:
    if audio.dim() == 2:
        audio = audio.squeeze(0)

    mel_transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=16000,
        n_fft=400,
        hop_length=160,
        win_length=400,
        n_mels=n_mels,
        center=True,
        power=2.0,
        norm="slaney",
        mel_scale="slaney",
    )
    mel = mel_transform(audio.float())
    mel = torch.clamp(mel, min=1e-10).log10()
    return mel.unsqueeze(0)


__all__ = ["Tokenizer", "log_mel_spectrogram"]
