import os
import re
import sys
import zipfile
import UnityPy
from UnityPy.enums import BuildTarget, TextureFormat
from UnityPy.files import SerializedFile

ASTC_MAP = {
    "4": TextureFormat.ASTC_RGBA_4x4,
    "6": TextureFormat.ASTC_RGBA_6x6,
    "8": TextureFormat.ASTC_RGBA_8x8,
    "12": TextureFormat.ASTC_RGBA_12x12,
}

SKIP_FORMATS = {
    TextureFormat.ASTC_RGBA_4x4, TextureFormat.ASTC_RGBA_5x5,
    TextureFormat.ASTC_RGBA_6x6, TextureFormat.ASTC_RGBA_8x8,
    TextureFormat.ASTC_RGBA_10x10, TextureFormat.ASTC_RGBA_12x12,
    TextureFormat.ASTC_RGB_4x4, TextureFormat.ASTC_RGB_6x6,
    TextureFormat.ASTC_RGB_8x8, TextureFormat.ASTC_RGB_12x12,
    TextureFormat.PVRTC_RGB2, TextureFormat.PVRTC_RGBA2,
    TextureFormat.PVRTC_RGB4, TextureFormat.PVRTC_RGBA4,
}

def rename_android_dir(path_str: str) -> str:
    return re.sub(r'(?<![a-zA-Z0-9])android(?![a-zA-Z0-9])', 'ios', path_str, flags=re.IGNORECASE)

def convert_bytes(raw_bytes: bytes, astc_block: str = "6") -> bytes:
    try:
        env = UnityPy.load(raw_bytes)
    except Exception:
        return raw_bytes

    if not env.objects:
        return raw_bytes

    target_fmt = ASTC_MAP.get(astc_block, TextureFormat.ASTC_RGBA_6x6)

    for f in env.files.values():
        if isinstance(f, SerializedFile):
            f.target_platform = BuildTarget.iOS
        elif hasattr(f, "files"):
            for sub in f.files.values():
                if isinstance(sub, SerializedFile):
                    sub.target_platform = BuildTarget.iOS

    for obj in env.objects:
        if obj.type.name == "Texture2D":
            try:
                tex = obj.read()
                if tex.m_Width > 0 and tex.m_Height > 0 and tex.m_TextureFormat not in SKIP_FORMATS:
                    img = tex.image
                    tex.set_image(img, target_format=target_fmt)
                    tex.save()
            except Exception:
                pass

    try:
        return env.file.save(packer="lz4")
    except Exception:
        return raw_bytes

def main():
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    astc_block = sys.argv[3] if len(sys.argv) > 3 else "6"
    rename_dirs = (sys.argv[4].lower() == "true") if len(sys.argv) > 4 else True

    if input_path.lower().endswith(".zip"):
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if not item.filename.endswith("/"):
                    new_name = rename_android_dir(item.filename) if rename_dirs else item.filename
                    zout.writestr(new_name, convert_bytes(zin.read(item.filename), astc_block))
    else:
        with open(input_path, "rb") as f:
            data = convert_bytes(f.read(), astc_block)
        with open(output_path, "wb") as f:
            f.write(data)

if __name__ == "__main__":
    main()
