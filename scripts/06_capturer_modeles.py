"""
06_capturer_modeles.py : Rend chaque modèle du Modeleur graphique (03_qgis/modeles/*.model3) en image PNG,
comme la commande « Exporter en image » du Modeleur, dans 00_docs/modeles/. Les images illustrent le README.

Usage (PowerShell, depuis le dossier du projet, QGIS peut rester fermé) :
    & "C:\\Program Files\\QGIS 3.34.12\\bin\\python-qgis-ltr.bat" scripts\\06_capturer_modeles.py
"""
import sys
from pathlib import Path

from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingModelAlgorithm
from qgis.gui import QgsModelGraphicsScene
from qgis.PyQt.QtCore import QRectF, Qt
from qgis.PyQt.QtGui import QImage, QPainter

RACINE = Path(__file__).resolve().parent.parent
MODELES = RACINE / "03_qgis" / "modeles"
SORTIE = RACINE / "00_docs" / "modeles"
ECHELLE = 2   # rendu deux fois plus dense, net sur les écrans haute résolution
MARGE = 24    # blanc autour du schéma, en unités de scène


def initialiser_traitements():
    """Le modèle doit retrouver ses algorithmes (natifs, GDAL) pour dessiner entrées et sorties."""
    sys.path.append(str(Path(QgsApplication.prefixPath()) / "python" / "plugins"))
    from processing.core.Processing import Processing
    from qgis.analysis import QgsNativeAlgorithms
    Processing.initialize()
    if not QgsApplication.processingRegistry().providerById("native"):
        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())


def capturer(chemin, contexte):
    modele = QgsProcessingModelAlgorithm()
    if not modele.fromFile(str(chemin)):
        raise RuntimeError(f"modèle illisible : {chemin}")
    scene = QgsModelGraphicsScene()
    scene.setFlag(QgsModelGraphicsScene.FlagHideControls)  # sans les boutons d'édition, comme l'export du Modeleur
    scene.setModel(modele)
    scene.createItems(modele, contexte)
    cadre = scene.itemsBoundingRect().adjusted(-MARGE, -MARGE, MARGE, MARGE)
    image = QImage(int(cadre.width() * ECHELLE), int(cadre.height() * ECHELLE), QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.white)  # résolution laissée à 96 dpi : sinon les polices en points grossiraient deux fois
    peintre = QPainter(image)
    peintre.setRenderHint(QPainter.Antialiasing)
    peintre.setRenderHint(QPainter.TextAntialiasing)
    scene.render(peintre, QRectF(0, 0, image.width(), image.height()), cadre)
    peintre.end()
    sortie = SORTIE / f"{chemin.stem}.png"
    if not image.save(str(sortie)):
        raise RuntimeError(f"écriture impossible : {sortie}")
    return sortie, modele.displayName(), image.width(), image.height()


if __name__ == "__main__":
    app = QgsApplication([], True)  # interface graphique requise par la scène du Modeleur
    app.initQgis()
    initialiser_traitements()
    SORTIE.mkdir(parents=True, exist_ok=True)
    contexte = QgsProcessingContext()
    for chemin in sorted(MODELES.glob("*.model3")):
        sortie, nom, l, h = capturer(chemin, contexte)
        print(f"{sortie.relative_to(RACINE)}  {l} x {h}  {nom}", flush=True)
    app.exitQgis()
