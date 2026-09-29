# 端到端测试脚本：上传中文音频 → 真实转录 → 返回文字
import json
import uuid
import urllib.request

BASE = "http://127.0.0.1:8000"


def post_multipart(url, fields, file_field, file_path):
    boundary = uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'
        ).encode("utf-8")
    fname = file_path.replace("\\", "/").split("/")[-1]
    body += (
        f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
        f'filename="{fname}"\r\nContent-Type: audio/wav\r\n\r\n'
    ).encode("utf-8")
    with open(file_path, "rb") as f:
        body += f.read()
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))


# 第 1 步：上传音频
up = post_multipart(
    f"{BASE}/api/meeting/upload",
    {"title": "ASR转录测试会议"},
    "audio",
    r"C:\Users\Lenovo\AppData\Local\Temp\test-chinese.wav",
)
print("① 上传:", up["message"], "| id =", up["id"], "|", up["audio_path"])

# 第 2 步：真实调用百炼 ASR 转录
req = urllib.request.Request(
    f"{BASE}/api/meeting/{up['id']}/transcribe", data=b"", method="POST"
)
resp = json.loads(urllib.request.urlopen(req, timeout=300).read().decode("utf-8"))
print("② 转录:", resp["message"], "| status =", resp["status"])
print("③ 识别文字:", resp["transcript"])
