import numpy as np
import soundfile as sf
from librosa import load
import soxr

def to_mono(y):
    if y.ndim > 1:
        y = np.mean(y, axis=tuple(range(y.ndim - 1)))
    return y


def fix_length(data, *, size, axis=-1, **kwargs):
    kwargs.setdefault("mode", "constant")

    n = data.shape[axis]

    if n > size:
        slices = [slice(None)] * data.ndim
        slices[axis] = slice(0, size)
        return data[tuple(slices)]

    elif n < size:
        lengths = [(0, 0)] * data.ndim
        lengths[axis] = (0, size - n)
        return np.pad(data, lengths, **kwargs)

    return data


def resample(
    y: np.ndarray,
    *,
    orig_sr: float,
    target_sr: float,
    res_type: str = "soxr_hq",
    fix: bool = True,
    scale: bool = False,
    axis: int = -1,
    **kwargs,
):
    ratio = float(target_sr) / orig_sr
    n_samples = int(np.ceil(y.shape[axis] * ratio))
    y_hat = np.apply_along_axis(
            soxr.resample,
            axis=axis,
            arr=y,
            in_rate=orig_sr,
            out_rate=target_sr,
            quality=res_type,
        )

    if fix:
        y_hat = fix_length(y_hat, size=n_samples, **kwargs)

    if scale:
        y_hat /= np.sqrt(ratio)

    return np.asarray(y_hat, dtype=y.dtype)


def load_audio(filepath, sr):
    y,sr_native=sf.read(filepath)
    y = to_mono(y)
    if sr !=sr_native and sr is not None:
        y = resample(y, orig_sr=sr_native, target_sr=sr,)
    return y,sr
