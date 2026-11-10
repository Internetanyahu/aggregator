from pathlib import Path
import re, subprocess, tempfile

html=Path("index.html").read_text(encoding="utf-8")
scripts=re.findall(r"<script>(.*?)</script>",html,re.S)
if not scripts:
    raise SystemExit("No inline application script found")
with tempfile.NamedTemporaryFile("w",suffix=".js",encoding="utf-8") as f:
    f.write("\n".join(scripts)); f.flush()
    subprocess.run(["node","--check",f.name],check=True)
print("Inline JavaScript syntax: OK")
