import sys
import cv2
import numpy as np
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QLineEdit, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
import socket
import threading
from PIL import ImageGrab

class RemoteDesktopClient(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Remote Desktop Client")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.image_label)

        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("Enter IP address (127.0.0.1 for local)")
        self.central_layout.addWidget(self.ip_input)

        self.connect_button = QPushButton("Connect", self)
        self.connect_button.clicked.connect(self.connect_to_server)
        self.central_layout.addWidget(self.connect_button)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_remote_image)

        self.socket = None

    def connect_to_server(self):
        ip_address = self.ip_input.text()
        port = 5555

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip_address, port))
            self.timer.start(1000 // 30)  # Update every 30 frames per second
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Unable to connect to the server: {e}")

    def update_remote_image(self):
        if self.socket:
            try:
                # Capture the desktop image
                screenshot = ImageGrab.grab()
                screenshot_np = np.array(screenshot)
                screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2RGB)

                # Encode the image to JPEG format
                _, encoded_image = cv2.imencode('.jpg', screenshot_cv)
                image_data = encoded_image.tobytes()

                # Send the image size first
                message_length = len(image_data).to_bytes(4, byteorder='big')
                self.socket.sendall(message_length)

                # Send the image data
                self.socket.sendall(image_data)

                # Display the image in the GUI
                h, w, ch = screenshot_cv.shape
                bytes_per_line = ch * w
                q_image = QPixmap.fromImage(QtGui.QImage(screenshot_cv.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888))
                self.image_label.setPixmap(q_image)
            except Exception as e:
                print(f"Error: {e}")
                self.socket.close()
                self.timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = RemoteDesktopClient()
    client.show()
    sys.exit(app.exec_())
