from tkinter import N
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from typing import List
import os
import sys

PHOTO_EXTENSIONS = ["jpg", "JPG", "jpeg", "JPEG"]
PRELOAD_COUNT = 100

class Viewer(QtWidgets.QWidget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = QtWidgets.QLabel(self)
        self.path: str = None
        self.filenames: List[str] = []
        self.load_mutexes: List[QtCore.QMutex] = []
        self.pixmaps: List[QtGui.QPixmap] = []
        self.scaled: List[QtGui.QPixmap] = []
        self.current_index: int = None
        self.thread_pool = QtCore.QThreadPool()
        self.loads = set()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        print("Resizing %d %d" % (self.width(), self.height()))
        self.label.resize(self.width(), self.height())
        self.scaled = [None] * len(self.scaled)
        if self.current_index is not None:
            self.switch(self.current_index)
        return super().resizeEvent(event)

    def switch(self, new_index: int):
        print("Switching to", self.filenames[new_index])
        self.current_index = new_index
        self.thread_pool.start(self.preload)
        self.load(new_index)
        if self.scaled[new_index] is None:
            self.scaled[new_index] = self.pixmaps[new_index].scaled(
                self.width(), self.height(),
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                transformMode=Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(self.scaled[new_index])

    @pyqtSlot()
    def preload(self):
        # The current_index one is loaded in main thread if needed.
        start = self.current_index + 1
        stop = min(self.current_index + PRELOAD_COUNT, len(self.filenames))
        for index in range(start, stop):
            self.load(index)

    def load(self, index: int):
        locker = QtCore.QMutexLocker(self.load_mutexes[index])
        if self.pixmaps[index] is None:
            full_path = os.path.join(self.path, self.filenames[index])
            self.pixmaps[index] = QtGui.QPixmap(full_path)

    def openDir(self, path: str):
        print("Opening ", path)
        self.path = path
        self.filenames = []
        self.pixmaps = []
        self.load_mutexes = []
        for filename in sorted(os.listdir(path)):
            if filename.split('.')[-1] in PHOTO_EXTENSIONS:
                self.filenames.append(filename)
                self.pixmaps.append(None)
                self.scaled.append(None)
                self.load_mutexes.append(QtCore.QMutex())
        if self.filenames:
            self.switch(0)
        else:
            self.current_index = None

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        event.accept()
        if event.key() == Qt.Key.Key_Escape.value:
            self.close()
        if self.current_index is not None:
            if event.key() == Qt.Key.Key_Right.value:
                self.switch((self.current_index + 1) % len(self.filenames))
            if event.key() == Qt.Key.Key_Left.value:
                self.switch((self.current_index - 1) % len(self.filenames))
        return super().keyPressEvent(event)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Viewer()
    window.showMaximized()
    if os.path.isdir(sys.argv[-1]):
        window.openDir(sys.argv[-1])
    app.exec()