import re
import UnityPy
from UnityPy.enums import BuildTarget, TextureFormat
from UnityPy.files import SerializedFile

IOS_SUPPORTED_FORMATS = {
    TextureFormat.ASTC_RGBA_4x4,
    TextureFormat.ASTC_RGBA_5x5,
    TextureFormat.ASTC_RGBA_6x6,
    TextureFormat.ASTC_RGBA_8x8,
    TextureFormat.ASTC_RGB_4x4,
    TextureFormat.ASTC_RGB_6x6,
    TextureFormat.RGBA32,
    TextureFormat.ARGB32,
    TextureFormat.RGB24,
}

def fix_path(path_str: str) -> str:
    # ប្តូរពាក្យ android ទៅ ios ក្នុងឈ្មោះ Folder និង Path ខាងក្នុង
    return re.sub(r'(?<![a-zA-Z0-9])android(?![a-zA-Z0-9])', 'ios', path_str, flags=re.IGNORECASE)

def patch_serialized_file(sf: SerializedFile):
    sf.target_platform = BuildTarget.iOS
    if hasattr(sf, "externals"):
        for ext in sf.externals:
            if getattr(ext, "path", None):
                ext.path = fix_path(ext.path)

def convert_bundle(raw_bytes: bytes) -> bytes:
    try:
        env = UnityPy.load(raw_bytes)
    except Exception:
        return raw_bytes

    if not env.objects:
        return raw_bytes

    # ១. កែ target_platform និង externals
    for f in env.files.values():
        if isinstance(f, SerializedFile):
            patch_serialized_file(f)
        elif hasattr(f, "files"):
            for sub in f.files.values():
                if isinstance(sub, SerializedFile):
                    patch_serialized_file(sub)

    # ២. បំប្លែង Texture2D ទៅ ASTC_RGBA_6x6
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            try:
                tex = obj.read()
                if tex.m_Width > 0 and tex.m_Height > 0 and tex.m_TextureFormat not in IOS_SUPPORTED_FORMATS:
                    img = tex.image
                    tex.set_image(img, target_format=TextureFormat.ASTC_RGBA_6x6)
                    tex.save()
            except Exception as e:
                print(f"[Warning] មិនអាចបំប្លែង Texture: {e}")

    try:
        return env.file.save(packer="lz4")
    except Exception:
        return raw_bytes
