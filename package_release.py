"""Zip the PyInstaller output into one portable release asset."""
from pathlib import Path
import platform
from zipfile import ZipFile, ZIP_DEFLATED

system=platform.system().lower()
name=f"Between-{system}-{platform.machine()}"
source=Path("dist/Between.app") if system=="darwin" else Path("dist/Between")
if not source.is_dir():raise SystemExit(f"Build output is missing: {source}")
Path("release").mkdir(exist_ok=True)
with ZipFile(Path("release")/f"{name}.zip","w",ZIP_DEFLATED) as bundle:
    for item in source.rglob("*"):
        if item.is_file():bundle.write(item,item.relative_to(source.parent))
print(f"Created release/{name}.zip")
