import numpy as np
import soundfile as sf
import soxr

# obtained form librosa


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


def get_rms(
    y,
    frame_length=2048,
    hop_length=512,
    pad_mode="constant",
):
    padding = (int(frame_length // 2), int(frame_length // 2))
    y = np.pad(y, padding, mode=pad_mode)

    axis = -1
    # put our new within-frame axis at the end for now
    out_strides = y.strides + tuple([y.strides[axis]])
    # Reduce the shape on the framing axis
    x_shape_trimmed = list(y.shape)
    x_shape_trimmed[axis] -= frame_length - 1
    out_shape = tuple(x_shape_trimmed) + tuple([frame_length])
    xw = np.lib.stride_tricks.as_strided(y, shape=out_shape, strides=out_strides)
    if axis < 0:
        target_axis = axis - 1
    else:
        target_axis = axis + 1
    xw = np.moveaxis(xw, -1, target_axis)
    # Downsample along the target axis
    slices = [slice(None)] * xw.ndim
    slices[axis] = slice(0, None, hop_length)
    x = xw[tuple(slices)]

    # Calculate power
    power = np.mean(np.abs(x) ** 2, axis=-2, keepdims=True)

    return np.sqrt(power)


def remove_opening_silence(audio, sr, padding_begin=0.1, padding_fin=0.2, threshold_db=-27):
    # Padding(sec) is actually margin of safety
    hop_length = 512
    rms_list = get_rms(audio, hop_length=hop_length).squeeze(0)
    threshold = 10 ** (threshold_db / 20.0)
    for i, rms in enumerate(rms_list):
        if rms >= threshold:
            break
    for j, rms in enumerate(reversed(rms_list)):
        if rms >= threshold:
            break
    cutting_point1 = max(i * hop_length - int(padding_begin * sr), 0)
    cutting_point2 = min((rms_list.shape[-1] - j) * hop_length + int(padding_fin * sr), audio.shape[-1])
    audio = audio[cutting_point1:cutting_point2]
    return audio


def load_audio(filepath, sr=None):
    y, sr_native = sf.read(filepath)
    y = to_mono(y)
    if sr != sr_native and sr not in [None, 0]:
        y = resample(y, orig_sr=sr_native, target_sr=sr)
        return y, sr
    else:
        return y, sr_native
