"""OBS 游戏查词脚本的纯逻辑部分，不依赖 OBS 和 Windows，方便单测。"""
import hashlib
import json
import re
import urllib.request

from PIL import Image, ImageOps

HASH_SIZE = (32, 18)


def frame_signature(img):
    """缩成小灰度图再比较，忽略压缩噪点。"""
    small = img.convert('L').resize(HASH_SIZE)
    return list(small.getdata())


def frames_differ(a, b, threshold=6):
    if a is None or b is None:
        return True
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a) > threshold


class StableChange:
    """画面变化后保持不变 settle 秒才触发一次，避免对白逐字显示时反复 OCR。"""

    def __init__(self, settle=0.4):
        self.settle = settle
        self._last = None
        self._changed_at = None
        self._fired = True

    def feed(self, sig, now):
        if frames_differ(self._last, sig):
            self._last = sig
            self._changed_at = now
            self._fired = False
            return False
        if not self._fired and now - self._changed_at >= self.settle:
            self._fired = True
            return True
        return False


def crop_region(img, region):
    """region 为 (left, top, right, bottom) 的 0-1 比例，None 表示整幅。"""
    if not region:
        return img
    w, h = img.size
    l, t, r, b = region
    return img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))


def prepare_for_ocr(img, scale=2.5):
    """灰度 + 拉伸对比度 + 放大。采集卡画面偏糊，实测 Windows OCR 相似度 0.79 -> 0.97；二值化反而会破坏笔画。"""
    gray = ImageOps.autocontrast(img.convert('L'), cutoff=2)
    return gray.resize((int(gray.width * scale), int(gray.height * scale)), Image.LANCZOS).convert('RGB')


def clean_ocr_text(text):
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'\s*\n\s*', ' ', text)
    return re.sub(r'\s{2,}', ' ', text).strip()


def looks_like_dialogue(text):
    """过滤纯符号和 OCR 噪声：至少两个字母词。"""
    return len(re.findall(r'[A-Za-z]{2,}', text)) >= 2


def format_items(items, max_chars=60):
    lines = []
    for it in items:
        first = (it['translation'] or '').strip().split('\n')[0]
        lines.append(f"{it['surface']}  {first[:max_chars]}")
    return '\n'.join(lines)


def post_lookup(server, text, game, timeout=5):
    req = urllib.request.Request(
        f"{server.rstrip('/')}/api/game/lookup",
        data=json.dumps({'text': text, 'game': game}).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def text_digest(text):
    return hashlib.md5(text.lower().encode()).hexdigest()


def parse_hotkey(name):
    """'F9' -> 0x78，单个字母或数字取其 ASCII 码；Windows 虚拟键码与此一致。"""
    name = name.strip().upper()
    if re.fullmatch(r'F([1-9]|1[0-2])', name):
        return 0x6F + int(name[1:])
    if re.fullmatch(r'[A-Z0-9]', name):
        return ord(name)
    raise ValueError(f'不支持的热键: {name!r}，请用 F1-F12 或单个字母/数字')


class EdgeTrigger:
    """按住不放只算一次按下。"""

    def __init__(self):
        self._down = False

    def pressed(self, is_down):
        fired = is_down and not self._down
        self._down = is_down
        return fired
