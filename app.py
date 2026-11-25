import io
import os
import zipfile
from flask import Flask, render_template_string, request, send_file
from converter import convert_bundle, fix_path

app = Flask(__name__)

UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLBB Script Converter (Android ➔ iOS)</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0b1120; color: #f1f5f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #1e293b; padding: 30px; border-radius: 16px; width: 90%; max-width: 440px; box-shadow: 0 12px 30px rgba(0,0,0,0.5); text-align: center; }
        h1 { font-size: 20px; color: #38bdf8; margin-bottom: 8px; }
        p { font-size: 13px; color: #94a3b8; margin-bottom: 20px; }
        input[type="file"] { background: #0f172a; padding: 14px; border-radius: 8px; border: 1px dashed #475569; width: 100%; box-sizing: border-box; color: #e2e8f0; margin-bottom: 18px; }
        button { background: #0284c7; color: #fff; border: none; padding: 13px; width: 100%; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; }
        button:hover { background: #0369a1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MLBB Android ➔ iOS Converter</h1>
        <p>ជ្រើសរើសឯកសារ .zip ឬ .unity3d ដើម្បីបំប្លែង</p>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="files" multiple required>
            <button type="submit">ចាប់ផ្តើមបំប្លែង (Convert)</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        files = [f for f in request.files.getlist("files") if f.filename]
        if not files:
            return "សូមជ្រើសរើសឯកសារ!", 400

        # ករណី Upload ឯកសារ .zip
        if len(files) == 1 and files.filename.lower().endswith(".zip"):
            in_buf = io.BytesIO(files.read())
            out_buf = io.BytesIO()
            with zipfile.ZipFile(in_buf, "r") as zin, zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zout:
                for info in zin.infolist():
                    if not info.is_dir():
                        zout.writestr(fix_path(info.filename), convert_bundle(zin.read(info.filename)))
            out_buf.seek(0)
            name = os.path.splitext(files.filename)
            return send_file(out_buf, as_attachment=True, download_name=f"{name}_iOS.zip")

        # ករណី Upload ឯកសារធម្មតា ១ ឬច្រើន
        if len(files) == 1:
            f = files
            return send_file(io.BytesIO(convert_bundle(f.read())), as_attachment=True, download_name=fix_path(f.filename))

        out_buf = io.BytesIO()
        with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for f in files:
                zout.writestr(fix_path(f.filename), convert_bundle(f.read()))
        out_buf.seek(0)
        return send_file(out_buf, as_attachment=True, download_name="Converted_iOS.zip")

    return render_template_string(UI_TEMPLATE)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
