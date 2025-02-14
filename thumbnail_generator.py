from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.gui import QgsMessageBar
from qgis.core import QgsProject, edit
import os
import re
import requests
from PIL import Image

class ThumbnailGenerator:
    def __init__(self, iface):
        """Costruttore del plugin"""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.menu = None
        self.action = None

    def initGui(self):
        """Inizializza l'interfaccia del plugin"""
        self.menu = self.iface.mainWindow().menuBar().addMenu("Thumbnail Generator")
        self.action = QAction("Generate Thumbnails", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.menu.addAction(self.action)

    def unload(self):
        """Rimuove il plugin dall'interfaccia"""
        if self.menu:
            self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())

    def run(self):
        """Esegue la funzione principale del plugin"""
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.critical(None, "Error", "No layer selected!")
            return

        thumbnail_folder = QFileDialog.getExistingDirectory(None, "Select Thumbnail Folder")
        if not thumbnail_folder:
            return

        image_fields = ["image1", "image2"]
        image_url_fields = ["thumbnails_url", "thumbnails_url2"]
        thumbnail_fields = ["thumbnail_path", "thumbnail_path2"]

        if not os.path.exists(thumbnail_folder):
            os.makedirs(thumbnail_folder)

        def get_drive_id(url):
            match = re.search(r'(?:id=|/d/)([\w-]+)', str(url))
            return match.group(1) if match else None

        def get_direct_link(url):
            file_id = get_drive_id(url)
            if file_id:
                return f"https://drive.google.com/uc?export=download&id={file_id}"
            return None

        with edit(layer):
            for feature in layer.getFeatures():
                for image_field, image_url_field, thumbnail_field in zip(image_fields, image_url_fields, thumbnail_fields):
                    image_url = feature[image_url_field]
                    if image_url:
                        direct_link = get_direct_link(image_url)
                        if not direct_link:
                            continue
                        try:
                            response = requests.get(direct_link, stream=True)
                            if response.status_code == 200:
                                image_path = os.path.join(thumbnail_folder, f"{feature.id()}_{thumbnail_field}.jpg")
                                with open(image_path, "wb") as f:
                                    f.write(response.content)
                                with Image.open(image_path) as img:
                                    img.thumbnail((100, 100))
                                    img.save(image_path)
                                feature[thumbnail_field] = image_path
                                layer.updateFeature(feature)
                        except Exception as e:
                            print(f"Error: {e}")
        QMessageBox.information(None, "Success", "Thumbnails generated successfully!")

