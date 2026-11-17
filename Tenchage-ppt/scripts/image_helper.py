"""
Tenchage-ppt v3.9 · 配图能力辅助
==================================
封装「为 PPT 版式生成配图」的标准流程。

⚠️ 关键设计：WorkBuddy 内置 ImageGen 是 agent 级工具（deferred tool），
   Python 脚本无法直接调用。因此本模块负责：
     1. 收集版式中声明的配图需求（prompt + 尺寸 + 目标路径）
     2. 导出为 image_manifest.json，供主 agent（哈小助）读取后逐张调 ImageGen 生成
     3. 提供 fallback 占位图生成（生成失败 / 未生图时不至于空白）
     4. 提供 crop_cover 工具，把任意图裁成版式需要的宽高比（object-fit: cover 效果）

   标准用法（主 agent 侧）：
     a. 跑版式脚本（dry_run=True）→ 产出 image_manifest.json
     b. 主 agent 读取 manifest，对每条 prompt 调用 ImageGen，把图存到 manifest 指定路径
     c. 再跑一次版式脚本（正式）→ 图已就位，直接嵌入
"""
import json
import os
from pathlib import Path


# ============================================================
# 配图需求收集器
# ============================================================
class ImageManifest:
    """收集一份 PPT 中所有配图需求，导出给主 agent 生图"""

    def __init__(self, project_dir, images_subdir='images'):
        self.project_dir = Path(project_dir)
        self.images_dir = self.project_dir / images_subdir
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.entries = []

    def add(self, name, prompt, aspect_ratio='4:3', width=1024):
        """
        登记一张配图需求。

        参数：
            name         : 图片文件名（不含扩展名），如 'store_scene'
            prompt       : 文生图提示词（中英文均可，建议英文更稳）
            aspect_ratio : 宽高比 '4:3' / '16:9' / '1:1' / '3:4'
            width        : 渲染宽度像素

        返回：
            目标图片绝对路径（.png），版式里用这个路径嵌入
        """
        out_path = self.images_dir / f'{name}.png'
        self.entries.append({
            'name': name,
            'prompt': prompt,
            'aspect_ratio': aspect_ratio,
            'width': width,
            'path': str(out_path),
            'status': 'pending' if not out_path.exists() else 'ready',
        })
        return str(out_path)

    def export(self, manifest_path=None):
        """导出 manifest.json，返回路径"""
        if manifest_path is None:
            manifest_path = self.project_dir / 'image_manifest.json'
        Path(manifest_path).write_text(
            json.dumps(self.entries, ensure_ascii=False, indent=2),
            encoding='utf-8')
        return str(manifest_path)

    def pending(self):
        """返回还没生成的配图列表"""
        return [e for e in self.entries if not Path(e['path']).exists()]

    def all_ready(self):
        """是否所有配图都已就位"""
        return all(Path(e['path']).exists() for e in self.entries)


# ============================================================
# 占位图（生图失败 / dry_run 时兜底）
# ============================================================
def make_placeholder(out_path, width=1024, height=768,
                     label='', bg='#E8EEF7', fg='#9AA8BE'):
    """
    生成一张腾讯风格占位图（浅蓝底 + 居中说明文字 + 图片图标）。
    依赖 Pillow。
    """
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (width, height), bg)
    d = ImageDraw.Draw(img)

    # 中心画一个简单的"图片"图标（山+太阳）
    cx, cy = width // 2, height // 2
    icon_w = min(width, height) // 3
    x0, y0 = cx - icon_w // 2, cy - icon_w // 2
    x1, y1 = cx + icon_w // 2, cy + icon_w // 2
    d.rectangle([x0, y0, x1, y1], outline=fg, width=3)
    # 太阳
    d.ellipse([x0 + icon_w*0.15, y0 + icon_w*0.15,
               x0 + icon_w*0.35, y0 + icon_w*0.35], outline=fg, width=3)
    # 山
    d.polygon([(x0, y1), (x0 + icon_w*0.4, y0 + icon_w*0.5),
               (x0 + icon_w*0.6, y0 + icon_w*0.7), (x1, y1)],
              outline=fg, width=3)

    if label:
        try:
            font = ImageFont.truetype('msyh.ttc', size=max(16, width // 32))
        except Exception:
            font = ImageFont.load_default()
        bbox = d.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        d.text((cx - tw // 2, y1 + 20), label, fill=fg, font=font)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return str(out_path)


def ensure_images(manifest_entries, make_missing_placeholder=True):
    """
    确保 manifest 里每张图都存在；缺失的用占位图补上（可选）。
    返回缺失列表（生成占位后清空）。
    """
    missing = []
    for e in manifest_entries:
        p = Path(e['path'])
        if not p.exists():
            if make_missing_placeholder:
                ar = e.get('aspect_ratio', '4:3')
                w = e.get('width', 1024)
                try:
                    rw, rh = map(int, ar.split(':'))
                    h = int(w * rh / rw)
                except Exception:
                    h = int(w * 0.75)
                make_placeholder(str(p), width=w, height=h,
                                 label=e.get('name', ''))
            else:
                missing.append(e['name'])
    return missing


# ============================================================
# 图片裁剪（object-fit: cover）
# ============================================================
def crop_cover(src_path, out_path, target_w, target_h):
    """
    把图片裁成目标宽高比（居中裁剪，等同 CSS object-fit: cover）。
    用于把任意比例的配图填满版式里的图片框，不变形不留白。

    参数：
        src_path        : 源图路径
        out_path        : 输出路径
        target_w/h      : 目标宽高（像素，比例即可）
    """
    from PIL import Image
    img = Image.open(src_path).convert('RGB')
    sw, sh = img.size
    target_ratio = target_w / target_h
    src_ratio = sw / sh

    if src_ratio > target_ratio:
        # 源图更宽，按高缩放，裁宽
        new_h = sh
        new_w = int(sh * target_ratio)
        left = (sw - new_w) // 2
        box = (left, 0, left + new_w, new_h)
    else:
        # 源图更高，按宽缩放，裁高
        new_w = sw
        new_h = int(sw / target_ratio)
        top = (sh - new_h) // 2
        box = (0, top, new_w, top + new_h)

    cropped = img.crop(box)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cropped.save(out_path)
    return str(out_path)


# ============================================================
# 提示词模板（腾讯智慧零售场景常用）
# ============================================================
PROMPT_PRESETS = {
    'retail_store': 'A bright modern supermarket interior, a customer browsing dairy products on shelves, natural lighting, photorealistic, commercial photography style, warm tone',
    'delivery': 'A food delivery rider in uniform handing a package to a customer at an apartment door, daytime, photorealistic, commercial photography, friendly atmosphere',
    'ecommerce': 'Several e-commerce parcel boxes next to a smartphone showing an online shopping app, clean desk, soft daylight, photorealistic product photography',
    'mini_program': 'A hand holding a smartphone showing a membership mini-program interface in a cafe, cozy background, photorealistic, shallow depth of field',
    'office_meeting': 'A modern business meeting room with people discussing around a screen, professional, photorealistic, corporate photography',
    'data_center': 'A clean modern data visualization dashboard on a large screen, blue tone, professional tech atmosphere, photorealistic',
}


def preset_prompt(key, extra=''):
    """取预设提示词，可追加额外描述"""
    base = PROMPT_PRESETS.get(key, '')
    return (base + (', ' + extra if extra else '')).strip(', ')


if __name__ == '__main__':
    # 自测：生成占位图
    test_dir = Path('_img_test')
    test_dir.mkdir(exist_ok=True)
    make_placeholder(str(test_dir / 'ph.png'), 800, 600, label='到店成交')
    print('✓ placeholder:', test_dir / 'ph.png')
