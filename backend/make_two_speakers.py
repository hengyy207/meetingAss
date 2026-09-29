# 制作"两人对话"测试音频：
# 用同一个 TTS 合成两句话，分别升调/降调后拼接，模拟两个不同音色的人
import array
import wave

SP1 = r"C:\Users\Lenovo\AppData\Local\Temp\sp1.wav"
SP2 = r"C:\Users\Lenovo\AppData\Local\Temp\sp2.wav"
OUT = r"C:\Users\Lenovo\AppData\Local\Temp\two-speakers.wav"


def pitch_shift(src_path, speed):
    """按 speed 比例重采样改变音高（>1 升调，<1 降调），返回 (params, frames)"""
    with wave.open(src_path, "rb") as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())

    samples = array.array("h")  # 16bit 有符号
    samples.frombytes(frames)

    # 线性插值重采样：按 speed 抽取/插值后总长变化，写回原采样率即改变音高
    new_len = int(len(samples) / speed)
    out = array.array("h", bytes(2 * new_len))
    for i in range(new_len):
        pos = i * speed
        j = int(pos)
        frac = pos - j
        if j + 1 < len(samples):
            out[i] = int(samples[j] * (1 - frac) + samples[j + 1] * frac)
        elif j < len(samples):
            out[i] = samples[j]
    return params, out.tobytes()


# 说话人 1：升调（声音变尖），说话人 2：降调（声音变沉）
p1, f1 = pitch_shift(SP1, 1.25)
p2, f2 = pitch_shift(SP2, 0.80)

# 两段参数应一致（同一 TTS 合成），直接拼接写文件
with wave.open(OUT, "wb") as w:
    w.setparams(p1)
    w.writeframes(f1)
    w.writeframes(f2)

print("done:", OUT, "| params:", p1)
