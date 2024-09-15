# client_app.py

import sys
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QSlider, QListWidget, QListWidgetItem, QPushButton
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from storage_reader import StorageReader

class VideoPlayer(QWidget):
    def __init__(self, storage_reader: StorageReader):
        super().__init__()
        self.storage_reader = storage_reader
        self.current_frame_index = 0
        self.is_playing = False

        self.init_ui()
        self.update_frame()

    def init_ui(self):
        # Video display area
        self.capture_label = QLabel(self)
        self.capture_label.setFixedSize(640, 480)  # Adjust as needed

        # Progress slider
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMaximum(len(self.storage_reader.frame_indices) - 1)
        self.slider.sliderMoved.connect(self.slider_moved)

        # Data display area
        self.data_list = QListWidget(self)

        # Playback control buttons
        self.play_button = QPushButton('Play')
        self.pause_button = QPushButton('Pause')

        self.play_button.clicked.connect(self.play)
        self.pause_button.clicked.connect(self.pause)

        # Layouts
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.pause_button)

        capture_layout = QVBoxLayout()
        capture_layout.addWidget(self.capture_label)
        capture_layout.addWidget(self.slider)
        capture_layout.addLayout(control_layout)

        main_layout = QHBoxLayout()
        main_layout.addLayout(capture_layout)
        main_layout.addWidget(self.data_list)

        self.setLayout(main_layout)
        self.setWindowTitle('Video Player with Data Display')

        # Timer for playback
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

    def update_frame(self):
        frame = self.storage_reader.get_frame(self.current_frame_index)
        data = self.storage_reader.data[self.current_frame_index]

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert frame to QImage and display
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.capture_label.setPixmap(QPixmap.fromImage(q_img))

        # Update data display
        self.data_list.clear()
        for key, value in data.items():
            if isinstance(value, np.ndarray):
                value_str = np.array2string(value)
            else:
                value_str = str(value)
            item = QListWidgetItem(f"{key}: {value_str}")
            self.data_list.addItem(item)

        # Update slider position
        self.slider.blockSignals(True)
        self.slider.setValue(self.current_frame_index)
        self.slider.blockSignals(False)

    def play(self):
        if not self.is_playing:
            self.is_playing = True
            self.timer.start(33)  # Approx 30 fps

    def pause(self):
        if self.is_playing:
            self.is_playing = False
            self.timer.stop()

    def next_frame(self):
        if self.current_frame_index < len(self.storage_reader.frame_indices) - 1:
            self.current_frame_index += 1
            self.update_frame()
        else:
            self.pause()

    def slider_moved(self, position):
        self.current_frame_index = position
        self.update_frame()

def main():
    args = sys.argv
    app = QApplication(args)
    reader = StorageReader(args[1])
    player = VideoPlayer(reader)
    player.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
