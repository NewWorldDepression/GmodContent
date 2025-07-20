import os
import zipfile
import shutil
import tempfile
import requests

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
import winreg

# Locate the Garry's Mod addons directory
def find_gmod_addons_path():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Valve\\Steam") as key:
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
    except FileNotFoundError:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Valve\\Steam") as key:
                steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        except FileNotFoundError:
            return None

    candidates = [
        Path(steam_path) / "steamapps/common/GarrysMod/garrysmod/addons"
    ]

    try:
        with open(Path(steam_path) / "steamapps/libraryfolders.vdf", "r") as f:
            for line in f:
                if '"' in line and "path" in line:
                    path = line.split('"')[3].replace('\\\\', '\\')
                    lib_path = Path(path) / "steamapps/common/GarrysMod/garrysmod/addons"
                    candidates.append(lib_path)
    except FileNotFoundError:
        pass

    for p in candidates:
        if p.exists():
            return p
    return None

# Thread to download and install multiple zip files
class MultiZipInstallerThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, zip_urls, parent=None):
        super().__init__(parent)
        self.zip_urls = zip_urls

    def run(self):
        gmod_path = find_gmod_addons_path()
        if not gmod_path:
            self.status.emit("❌ Garry's Mod addons folder not found.")
            return

        total_files = len(self.zip_urls)
        temp_dir = Path(tempfile.gettempdir()) / "gmod_batch_addons"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            for index, url in enumerate(self.zip_urls):
                self.status.emit(f"🔄 Downloading file {index + 1} of {total_files}...")
                filename = f"addon_{index + 1}.zip"
                zip_path = temp_dir / filename

                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(zip_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)

                self.status.emit(f"📦 Extracting addon {index + 1}...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    extract_path = temp_dir / f"extracted_{index + 1}"
                    zip_ref.extractall(extract_path)

                    for item in os.listdir(extract_path):
                        src = extract_path / item
                        dst = gmod_path / item
                        if src.is_dir():
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                        else:
                            shutil.copy2(src, dst)

                self.progress.emit(int(((index + 1) / total_files) * 100))

            self.status.emit(f"✅ All 8 addons installed successfully in: {gmod_path}")
        except Exception as e:
            self.status.emit(f"❌ Error during install: {e}")

# GUI for multi-zip installer
class GModMultiInstaller(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GMod Addon Multi Installer")
        self.resize(420, 220)

        self.layout = QVBoxLayout()
        self.label = QLabel("Click 'Install' to download and install 8 addons.")
        self.progress = QProgressBar()
        self.button = QPushButton("Install 8 Addons")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        self.button.clicked.connect(self.install_addons)

    def install_addons(self):
        # Replace with your actual 8 ZIP file URLs (DigitalOcean Spaces or other HTTP hosts)
        zip_urls = [
            "https://gmodcontent.fra1.cdn.digitaloceanspaces.com/hl2ep2-content-gmodcontent.zip",
            "https://gmodcontent.fra1.cdn.digitaloceanspaces.com/hl2ep1-content-gmodcontent.zip",
            "https://gmodcontent.fra1.cdn.digitaloceanspaces.com/css-content-gmodcontent.zip",
            "https://gmodcontent.fra1.cdn.digitaloceanspaces.com/css-maps-gmodcontent.zip",
            "https://gmodcontent.fra1.cdn.digitaloceanspaces.com/hl2ep2-content-gmodcontent.zip",
            "https://gmodcontent.fra1.cdn.digitaloceanspaces.com/hl2ep1-content-gmodcontent.zip",
            "https://gmodcontent.fra1.cdn.digitaloceanspaces.com/css-content-gmodcontent.zip",
            "https://gmodcontent.fra1.cdn.digitaloceanspaces.com/css-maps-gmodcontent.zip",
        ]

        self.thread = MultiZipInstallerThread(zip_urls)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.status.connect(self.label.setText)
        self.thread.start()

# Start the GUI
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GModMultiInstaller()
    window.show()
    sys.exit(app.exec())
