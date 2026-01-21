from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidgetItem,
    QPushButton, QListWidget, QLabel, QFileDialog, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from pathlib import Path

from workers.worker import VideoWorker
from config import ProcessingOptions, SUPPORTED_FORMATS, settings, STATUS_PENDING, STATUS_WORKING, STATUS_DONE, STATUS_ERROR
from dictionary.translators import TRANSLATORS
from dictionary.languages import WHISPER_LANGS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Translator")
        self.setFixedSize(550, 600)
        self.setWindowIcon(QIcon("app/img/logo.png"))

        self.tasks = []
        self.current_worker = None

        self.output_label = QLabel("Output folder: not selected")
        self.output_dir = None
        saved_out = settings.value("output_dir")
        if saved_out:
            self.output_dir = Path(saved_out)
            self.output_label.setText(f"Output folder: {saved_out}")

        self.list = QListWidget()
        self.log = QLabel("Ready")

        self.translator_combo = QComboBox()
        self.translator_combo.setFixedWidth(135)
        self.translator_combo.addItems(TRANSLATORS.keys())
        self.translator_combo.currentTextChanged.connect(self.update_language_options)

        self.source_lang_combo = QComboBox()
        self.target_lang_combo = QComboBox()
        self.source_lang_combo.setFixedWidth(135)
        self.target_lang_combo.setFixedWidth(135)

        self.whisper_lang_combo = QComboBox()
        self.whisper_lang_combo.setFixedWidth(135)
        self.whisper_lang_combo.addItems(WHISPER_LANGS.keys())

        self.cb_source = QCheckBox("Save original subtitles")
        self.cb_target = QCheckBox("Save translated subtitles")
        self.cb_burn_hardsubs = QCheckBox("Burn-in Subtitles")
        self.cb_source.setChecked(ProcessingOptions.save_source_srt)
        self.cb_target.setChecked(ProcessingOptions.save_target_srt)
        self.cb_burn_hardsubs.setChecked(ProcessingOptions.burn_hardsubs)

        btn_add = QPushButton("Add videos")
        btn_add.setFixedWidth(135)
        btn_start = QPushButton("Start")
        btn_start.setFixedWidth(135)
        btn_remove = QPushButton("Remove selected")
        btn_remove.setFixedWidth(135)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedWidth(135)
        btn_cancel.clicked.connect(self.cancel)

        btn_output = QPushButton("Select output folder")
        btn_output.setFixedWidth(135)
        btn_output.clicked.connect(self.select_output_folder)

        btn_add.clicked.connect(self.add_videos)
        btn_start.clicked.connect(self.start)
        btn_remove.clicked.connect(self.remove_selected)

        vlayout = QVBoxLayout()
        vlayout.addWidget(self.list)
        vlayout.addSpacing(10)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_remove, alignment=Qt.AlignLeft)
        btn_layout.addWidget(btn_add, alignment=Qt.AlignRight)
        vlayout.addLayout(btn_layout)
        vlayout.addSpacing(20)

        vlayout.addWidget(QLabel("Recognition language:"))
        vlayout.addWidget(self.whisper_lang_combo)
        vlayout.addSpacing(20)

        hlayout = QHBoxLayout()

        trans_layot = QVBoxLayout()
        trans_layot.addWidget(QLabel("Translator:"))
        trans_layot.addWidget(self.translator_combo)
        trans_layot.setAlignment(Qt.AlignLeft)
        hlayout.addLayout(trans_layot)

        from_layot = QVBoxLayout()
        from_layot.addWidget(QLabel("From:"))
        from_layot.addWidget(self.source_lang_combo)
        from_layot.setAlignment(Qt.AlignCenter)
        hlayout.addLayout(from_layot)

        to_layot = QVBoxLayout()
        to_layot.addWidget(QLabel("To:"))
        to_layot.addWidget(self.target_lang_combo)
        to_layot.setAlignment(Qt.AlignRight)
        hlayout.addLayout(to_layot) 

        vlayout.addLayout(hlayout)
        vlayout.addSpacing(20)

        vlayout.addWidget(self.cb_source)
        vlayout.addWidget(self.cb_target)
        vlayout.addWidget(self.cb_burn_hardsubs)
        vlayout.addSpacing(10)

        output_layout = QHBoxLayout()
        output_layout.addWidget(btn_output, alignment=Qt.AlignLeft)
        output_layout.addWidget(self.output_label, alignment=Qt.AlignLeft)
        vlayout.addLayout(output_layout)
        vlayout.addSpacing(20)

        butt_btn_layout = QHBoxLayout()
        butt_btn_layout.addWidget(btn_start, alignment=Qt.AlignCenter)
        butt_btn_layout.addWidget(btn_cancel, alignment=Qt.AlignCenter)
        vlayout.addLayout(butt_btn_layout)

        vlayout.addWidget(self.log)

        container = QWidget()
        container.setLayout(vlayout)

        self.update_language_options(self.translator_combo.currentText())
        
        self.setCentralWidget(container)

    def add_videos(self):
        filter_str = "Video files (" + " ".join(f"*.{ext}" for ext in SUPPORTED_FORMATS) + ")"
        files, _ = QFileDialog.getOpenFileNames(self, "Select videos", filter=filter_str)

        for f in files:
            item = QListWidgetItem(f"{STATUS_PENDING} {Path(f).name}")
            item.setData(Qt.UserRole, Path(f))
            self.list.addItem(item)
            self.tasks.append(item)

    def remove_selected(self):
        row = self.list.currentRow()
        if row >= 0 and self.current_worker is None:
            self.list.takeItem(row)
            self.tasks.pop(row)

    def update_language_options(self, translator_name):
        self.source_lang_combo.clear()
        self.target_lang_combo.clear()

        translator_info = TRANSLATORS.get(translator_name)
        if not translator_info:
            return

        for lang_name in translator_info["langs"]:
            self.source_lang_combo.addItem(lang_name)

        for lang_name in translator_info["langs"]:
            self.target_lang_combo.addItem(lang_name)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_dir = Path(folder)
            self.output_label.setText(f"Output folder: {folder}")
            settings.setValue("output_dir", folder)

    def start(self):
        if self.current_worker or not self.tasks:
            return

        item = self.tasks.pop(0)
        video: Path = item.data(Qt.UserRole)

        item.setText(f"{STATUS_WORKING} {video.name}")

        translator_name = self.translator_combo.currentText()
        translator_info = TRANSLATORS.get(translator_name)
        if not translator_info:
            item.setText(f"{STATUS_ERROR} {video.name}")
            return

        whisper_lang_code = translator_info.get("whisper_langs", {}).get(
            self.whisper_lang_combo.currentText()
        )
        source_lang_code = translator_info["langs"].get(self.source_lang_combo.currentText())
        target_lang_code = translator_info["langs"].get(self.target_lang_combo.currentText())

        translator = translator_info["factory"](source_lang_code, target_lang_code)

        options = ProcessingOptions(
            save_source_srt=self.cb_source.isChecked(),
            save_target_srt=self.cb_target.isChecked(),
            burn_hardsubs=self.cb_burn_hardsubs.isChecked()
        )

        self.current_worker = VideoWorker(
            video,
            whisper_lang_code,
            source_lang_code,
            target_lang_code,
            translator,
            options,
            self.output_dir
        )

        self.current_worker.progress.connect(self.log.setText)
        self.current_worker.finished.connect(lambda _: self.on_finished(item))
        self.current_worker.error.connect(lambda _: self.on_error(item))
        self.current_worker.start()

    def on_finished(self, item):
        video = item.data(Qt.UserRole)
        item.setText(f"{STATUS_DONE} {video.name}")
        self.log.setText("Done")
        self.current_worker = None
        self.start()

    def on_error(self, item):
        video = item.data(Qt.UserRole)
        item.setText(f"{STATUS_ERROR} {video.name}")
        self.current_worker = None
        self.start()

    def cancel(self):
        if self.current_worker:
            self.current_worker.terminate()
            self.current_worker.wait()
            self.current_worker = None
    
        self.tasks.clear()
        self.list.clear()
        self.log.setText("Canceled")
