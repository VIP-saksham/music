import os
import aiofiles
import aiohttp
from PIL import Image

from config import YOUTUBE_IMG_URL


CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def resize_cover(img, size=(1920, 1080)):
    """
    Resize image to exact fullscreen size without distortion
    (center crop, professional look)
    """
    img_ratio = img.width / img.height
    target_ratio = size[0] / size[1]

    if img_ratio > target_ratio:
        new_height = size[1]
        new_width = int(new_height * img_ratio)
    else:
        new_width = size[0]
        new_height = int(new_width / img_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    left = (new_width - size[0]) // 2
    top = (new_height - size[1]) // 2
    right = left + size[0]
    bottom = top + size[1]

    return img.crop((left, top, right, bottom))


async def get_thumb(videoid, user_id):
    final_path = f"{CACHE_DIR}/{videoid}_{user_id}.png"

    if os.path.isfile(final_path):
        return final_path

    try:
        # 🔥 Direct highest quality YouTube thumbnails
        thumb_urls = [
            f"https://i.ytimg.com/vi/{videoid}/maxresdefault.jpg",
            f"https://i.ytimg.com/vi/{videoid}/hqdefault.jpg",
        ]

        image_bytes = None

        async with aiohttp.ClientSession() as session:
            for url in thumb_urls:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        break

        if not image_bytes:
            return YOUTUBE_IMG_URL

        temp_path = f"{CACHE_DIR}/temp_{videoid}.jpg"
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(image_bytes)

        img = Image.open(temp_path).convert("RGB")

        # 🎯 FULL SCREEN 1920×1080
        img = resize_cover(img, (1920, 1080))

        # 🔥 Save max quality (no compression tricks)
        img.save(final_path, "PNG", optimize=False)

        os.remove(temp_path)
        return final_path

    except Exception as e:
        print("THUMB ERROR:", e)
        return YOUTUBE_IMG_URL
