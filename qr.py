import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PIL import Image
import qrcode


def resize_background_image(background_path, target_size=(512, 512)):
    """多步調整背景圖大小，保持長寬比並填充到指定大小"""
    try:
        background = Image.open(background_path).convert("RGBA")

        # 獲取原始寬高
        bg_width, bg_height = background.size

        # 按比例調整
        scale = min(target_size[0] / bg_width, target_size[1] / bg_height)
        new_width = int(bg_width * scale)
        new_height = int(bg_height * scale)
        resized_background = background.resize((new_width, new_height), Image.LANCZOS)

        # 創建目標尺寸的空白圖像並填充
        final_background = Image.new("RGBA", target_size, (255, 255, 255, 0))
        paste_position = ((target_size[0] - new_width) // 2, (target_size[1] - new_height) // 2)
        final_background.paste(resized_background, paste_position)

        return final_background
    except Exception as e:
        raise ValueError(f"背景圖調整失敗: {e}")


def create_qrcode_with_image_background(data, background_path, output_dir, qr_size=(200, 200)):
    """生成二維碼並疊加到背景圖片"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="transparent").convert("RGBA")
        qr_image = qr_image.resize(qr_size, Image.LANCZOS)

        # 調整背景圖片大小
        resized_background = resize_background_image(background_path)

        # 計算二維碼粘貼位置
        bg_width, bg_height = resized_background.size
        qr_width, qr_height = qr_image.size
        position = ((bg_width - qr_width) // 2, (bg_height - qr_height) // 2)

        # 將二維碼粘貼到背景圖上
        resized_background.paste(qr_image, position, qr_image)

        # 保存生成的二維碼文件
        output_filename = f"qrcode_{os.path.basename(background_path)}.png"
        output_path = os.path.join(output_dir, output_filename)

        # 如果是 JPEG 格式，需轉換為 RGB 模式
        if resized_background.mode == 'RGBA':
            resized_background = resized_background.convert("RGB")  # 去除透明度通道

        resized_background.save(output_path)

        return output_path
    except Exception as e:
        raise ValueError(f"生成二維碼失敗: {e}")


class QRCodeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("二維碼生成器")
        self.setGeometry(100, 100, 600, 400)

        self.initUI()

    def initUI(self):
        # 主窗口
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 標籤
        self.label = QLabel("輸入二維碼內容：", self)
        self.text_input = QLineEdit(self)

        # 按鈕
        self.select_button = QPushButton("選擇背景圖片", self)
        self.select_button.clicked.connect(self.select_background)

        self.generate_button = QPushButton("生成二維碼", self)
        self.generate_button.clicked.connect(self.generate_qrcode)

        # 顯示二維碼的標籤
        self.qr_label = QLabel(self)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setFixedSize(250, 250)

        # 佈局
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text_input)
        self.layout.addWidget(self.select_button)
        self.layout.addWidget(self.generate_button)
        self.layout.addWidget(self.qr_label)

        self.background_path = None

    def select_background(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self, "選擇背景圖片", "", "圖片文件 (*.png *.jpg *.jpeg);;所有文件 (*)", options=options
        )
        if file_path:
            self.background_path = file_path
            QMessageBox.information(self, "背景圖片", f"已選擇背景圖片：{file_path}")

    def generate_qrcode(self):
        data = self.text_input.text()
        if not data:
            QMessageBox.warning(self, "錯誤", "請輸入二維碼內容！")
            return

        if not self.background_path:
            QMessageBox.warning(self, "錯誤", "請先選擇背景圖片！")
            return

        output_dir = os.getcwd()  # 保存文件的目錄
        try:
            result_path = create_qrcode_with_image_background(data, self.background_path, output_dir)
            self.display_qrcode(result_path)
            QMessageBox.information(self, "成功", f"二維碼已生成：{result_path}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))

    def display_qrcode(self, path):
        pixmap = QPixmap(path)
        self.qr_label.setPixmap(pixmap.scaled(self.qr_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QRCodeApp()
    window.show()
    sys.exit(app.exec_())
