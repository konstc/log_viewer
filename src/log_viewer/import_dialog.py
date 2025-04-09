""" Log viewer's import dialog window module """

import logging

import can
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QDialog, QMessageBox

from generated_ui import Ui_ImportDialog
from plotter import J1939DumpPlotter

class ImportWorker(QObject):
    """
    A worker to open given plotter
    """

    failed = pyqtSignal(str)
    finished = pyqtSignal()
    processed = pyqtSignal(int)

    def __init__(self, plotter: J1939DumpPlotter) -> None:
        """
        Constructs an ImportWorker to open given 'plotter' object
        """
        super().__init__()
        self._plotter = plotter

    @pyqtSlot()
    def run(self) -> None:
        """
        Processes opening of given plotter object
        """
        while not self._plotter.is_opened:
            if QThread.currentThread().isInterruptionRequested():
                return
            try:
                self._plotter.open()
                self.processed.emit(self._plotter.processed)
            except (ImportError, ValueError, can.io.blf.BLFParseError) as err:
                logging.error(err, exc_info=True)
                self.failed.emit(str(err))
                return
        self.finished.emit()

class ImportDialog(QDialog):
    """
    Dialog window with plotter's opening progress
    """

    def __init__(self, plotter: J1939DumpPlotter) -> None:
        """
        Constructs a ImportDialog with a given 'plotter'. Opening thread will
        start immediately after construction.
        """

        super().__init__()

        self._ui = Ui_ImportDialog()
        self._ui.setupUi(self)

        self._thread = QThread()
        self._worker = ImportWorker(plotter)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.failed.connect(self._import_failed)
        self._thread.finished.connect(self._import_finished)
        self._worker.processed.connect(self._update_processed)
        self._ui.cancelButton.clicked.connect(self.reject)
        self._thread.start()

    @pyqtSlot(int)
    def _update_processed(self, processed) -> None:
        """
        Processes 'processed' signal from the self._worker. Updates UI's 
        message counter.
        """
        self._ui.messageCount.setText(str(processed))

    @pyqtSlot(str)
    def _import_failed(self, err: str) -> None:
        """
        Processes 'failed' signal from the self._worker. Aborts import process.
        """
        QMessageBox.critical(None, "Import failed!", err)
        self.reject()

    @pyqtSlot()
    def _import_finished(self) -> None:
        """
        Processes 'finished' signal from the self._thread. Passes import
        process.
        """
        self._thread.deleteLater()
        self.accept()

    @pyqtSlot()
    def reject(self) -> None:
        """
        Aborts import process
        """
        self._thread.requestInterruption()
        self._thread.quit()
        self._thread.wait()
        return super().reject()
