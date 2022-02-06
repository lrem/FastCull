from PySide6 import QtCore
from PySide6.QtCore import Qt, Slot
from PySide6 import QtGui
from PySide6 import QtWidgets

from typing import List
import os
import sys
import time

PHOTO_EXTENSIONS = ["jpg", "JPG", "jpeg", "JPEG"]
PRELOAD_COUNT = 10

class Wrapper(QtCore.QRunnable):

    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        super().__init__()

    @Slot()
    def run(self):
        self.function(*self.args, **self.kwargs)

class Overlay(QtWidgets.QWidget):

    _height = 64

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = QtWidgets.QLabel(self)
        self.label.setStyleSheet("color: #FEFEFE; font: bold 32px; font-family: Impact")
        self.effect = QtWidgets.QGraphicsDropShadowEffect(self)
        self.effect.setOffset(0, 0)
        self.effect.setBlurRadius(30)
        self.effect.setColor(Qt.black)
        self.label.setGraphicsEffect(self.effect)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self.label.resize(self.width(), Overlay._height)
        return super().resizeEvent(event)
    
    def updateContent(self, protected: bool = False):
        text = ""
        if(protected):
            text += "  P"
        self.label.setText(text)

class Viewer(QtWidgets.QWidget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = QtWidgets.QStackedLayout()
        self.layout.setStackingMode(
            QtWidgets.QStackedLayout.StackingMode.StackAll)
        self.overlay = Overlay(parent=self)
        self.layout.addWidget(self.overlay)
        self.overlay.updateContent(protected=True)
        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)
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
        self.overlay.resize(self.width(), self.height())
        self.scaled = [None] * len(self.scaled)
        if self.current_index is not None:
            self.switch(self.current_index)
        return super().resizeEvent(event)

    def switch(self, new_index: int):
        print("Switching to", self.filenames[new_index])
        timing = [(time.time(), "start")]
        self.current_index = new_index
        self.preload()
        timing.append((time.time(), "launching preload"))
        self.load(new_index)
        timing.append((time.time(), "loading"))
        if self.scaled[new_index] is None:
            self.scaled[new_index] = self.pixmaps[new_index].scaled(
                self.width(), self.height(),
                aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
                mode=Qt.TransformationMode.SmoothTransformation)
        timing.append((time.time(), "scaling"))
        self.label.setPixmap(self.scaled[new_index])
        timing.append((time.time(), "displaying"))
        for i in range(1, len(timing)):
            print("%.2fs %s" % (timing[i][0] - timing[i-1][0], timing[i][1]))

    def preload(self):
        # The current_index one is loaded in main thread if needed.
        start = self.current_index + 1
        stop = min(self.current_index + PRELOAD_COUNT, len(self.filenames))
        for index in range(start, stop):
            self.thread_pool.start(Wrapper(self.load, index))

    def load(self, index: int):
        locker = QtCore.QMutexLocker(self.load_mutexes[index])
        if self.pixmaps[index] is None:
            full_path = os.path.join(self.path, self.filenames[index])
            self.pixmaps[index] = QtGui.QPixmap(full_path)
        locker.unlock()

    def openDir(self, path: str, start_file: str = None):
        print("Opening ", path)
        self.path = path
        self.filenames = []
        self.pixmaps = []
        self.load_mutexes = []
        start = time.time()
        for filename in sorted(os.listdir(path)):
            if filename.split('.')[-1] in PHOTO_EXTENSIONS:
                self.filenames.append(filename)
                self.pixmaps.append(None)
                self.scaled.append(None)
                self.load_mutexes.append(QtCore.QMutex())
        print("%.2fs %s" % (time.time() - start, "listing directory"))
        if start_file:
            self.switch(self.filenames.index(start_file))
        elif self.filenames:
            self.switch(0)
        else:
            self.current_index = None

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        event.accept()
        if event.key() == Qt.Key_Escape:
            self.close()
        if self.current_index is not None:
            if event.key() == Qt.Key.Key_Right:
                self.switch((self.current_index + 1) % len(self.filenames))
            if event.key() == Qt.Key.Key_Left:
                self.switch((self.current_index - 1) % len(self.filenames))
        return super().keyPressEvent(event)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Viewer()
    window.showMaximized()
    arg = sys.argv[-1]
    if os.path.isdir(arg):
        window.openDir(arg)
    elif os.path.isfile(arg):
        window.openDir(os.path.dirname(arg), os.path.basename(arg))
    else:
        print(arg, "does not seem to be a file or directory")
    app.exec()