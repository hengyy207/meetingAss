# 测试删除接口：上传一条测试会议 → 删除 → 确认列表和详情都查不到
import json
import uuid
import urllib.request
import urllib.error

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


def delete(url):
    req = urllib.request.Request(url, method="DELETE")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, (e.code, json.loads(e.read().decode("utf-8")))


# 1. 上传一条测试会议
up = post_multipart(
    f"{BASE}/api/meeting/upload",
    {"title": "待删除的测试会议"},
    "audio",
    r"C:\Users\Lenovo\AppData\Local\Temp\test-chinese.wav",
)
mid = up["id"]
print("① 上传成功 id =", mid)

# 2. 删除
res, err = delete(f"{BASE}/api/meeting/{mid}")
assert err is None, f"删除失败: {err}"
print("② 删除:", res["message"], "| id =", res["id"])

# 3. 再查详情应 404
_, err = delete(f"{BASE}/api/meeting/{mid}")  # 顺带测重复删除
assert err and err[0] == 404, f"预期 404，实际: {err}"
print("③ 重复删除返回 404:", err[1]["detail"])

# 4. 列表里确认已消失
lst = json.loads(urllib.request.urlopen(f"{BASE}/api/meeting").read().decode("utf-8"))
assert mid not in [m["id"] for m in lst], "列表中仍能查到已删除的会议"
print(f"④ 列表确认已删除（当前共 {len(lst)} 条）")

# 5. 删除不存在的 id 也应 404
_, err = delete(f"{BASE}/api/meeting/99999")
assert err and err[0] == 404, f"预期 404，实际: {err}"
print("⑤ 删除不存在的会议返回 404 ✓")

print("\n全部通过 ✓")
