# 端到端测试脚本：上传中文音频 → 真实转录 → AI 总结 → 返回结构化纪要
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


def post_json(url):
    req = urllib.request.Request(url, data=b"", method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=300).read().decode("utf-8"))


# 第 1 步：上传音频
up = post_multipart(
    f"{BASE}/api/meeting/upload",
    {"title": "全链路测试会议"},
    "audio",
    r"C:\Users\Lenovo\AppData\Local\Temp\test-chinese.wav",
)
print("① 上传:", up["message"], "| id =", up["id"])

# 第 2 步：真实转录（百炼 Fun-ASR）
tr = post_json(f"{BASE}/api/meeting/{up['id']}/transcribe")
print("② 转录:", tr["message"], "| status =", tr["status"])
print("   文字:", tr["transcript"])

# 第 3 步：AI 总结（MiMo）
sm = post_json(f"{BASE}/api/meeting/{up['id']}/summarize")
print("③ 总结:", sm["message"], "| status =", sm["status"])
print("   主题:", sm["summary"]["theme"])
print("   要点:", json.dumps(sm["summary"]["points"], ensure_ascii=False))
print("   任务:", json.dumps(sm["tasks"], ensure_ascii=False))

# 第 4 步：查详情确认入库
det = json.loads(urllib.request.urlopen(f"{BASE}/api/meeting/{up['id']}").read().decode("utf-8"))
assert det["summary"] and det["transcript"], "详情数据不完整"
print("④ 详情: status =", det["status"], "| summary/tasks/transcript 均已入库 ✓")
print("\n全部通过 ✓  会议 ID =", up["id"])
