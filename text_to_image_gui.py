import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QWidget, QLabel, QFileDialog, QProgressBar,
                           QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from convert_text_to_image import convert_file

class CuteButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont('맑은 고딕', 10))
        
class CuteFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFF0F5;
                border-radius: 15px;
                border: 2px solid #FFB6C1;
            }
        """)

class ConversionWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, input_dir):
        super().__init__()
        self.input_dir = input_dir
        
    def run(self):
        try:
            files = [f for f in os.listdir(self.input_dir) 
                    if os.path.isfile(os.path.join(self.input_dir, f)) and 
                    (f.lower().endswith('.txt') or os.path.splitext(f)[1] == '')]
            
            if not files:
                self.error.emit('변환할 텍스트 파일이 없습니다 🥺')
                return
                
            output_dir = os.path.join(os.path.dirname(self.input_dir), "output")
            os.makedirs(output_dir, exist_ok=True)
            
            total_files = len(files)
            for i, filename in enumerate(files, 1):
                try:
                    file_path = os.path.join(self.input_dir, filename)
                    image_file = convert_file(file_path)
                    
                    if image_file:
                        # 파일 이동
                        os.rename(file_path, os.path.join(output_dir, filename))
                        os.rename(image_file, os.path.join(output_dir, os.path.basename(image_file)))
                    
                    progress = int((i / total_files) * 100)
                    self.progress.emit(progress)
                    
                except Exception as e:
                    self.error.emit(f'파일 변환 중 오류 발생: {filename}\n{str(e)} 😢')
                    continue
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f'처리 중 오류가 발생했습니다: {str(e)} 😢')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('✨ 텍스트 → 이미지 변환기 ✨')
        self.setFixedSize(500, 300)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFF5F5;
            }
            QLabel {
                color: #FF69B4;
                font-family: '맑은 고딕';
                font-size: 11px;
            }
            QPushButton {
                background-color: #FFB6C1;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
            QPushButton:disabled {
                background-color: #FFC0CB;
            }
            QProgressBar {
                border: 2px solid #FFB6C1;
                border-radius: 5px;
                text-align: center;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #FF69B4;
                border-radius: 3px;
            }
        """)
        
        # 메인 위젯과 레이아웃
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        main_widget.setLayout(layout)
        
        # 타이틀 레이블
        title_label = QLabel('🎵 텍스트를 예쁜 이미지로 변환해드려요! 🎵')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 14px; font-weight: bold; margin: 10px;')
        layout.addWidget(title_label)
        
        # 내용을 담을 귀여운 프레임
        content_frame = CuteFrame()
        content_layout = QVBoxLayout()
        content_frame.setLayout(content_layout)
        
        # 설명 레이블
        info_label = QLabel('📁 텍스트 파일이 있는 폴더를 선택해주세요!\n💝 변환된 파일은 output 폴더에 저장됩니다')
        info_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(info_label)
        
        # 폴더 선택 영역
        folder_frame = QFrame()
        folder_layout = QHBoxLayout()
        folder_frame.setLayout(folder_layout)
        
        self.path_label = QLabel('선택된 폴더: 없음 😊')
        folder_layout.addWidget(self.path_label)
        
        select_btn = CuteButton('폴더 선택 📁')
        select_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(select_btn)
        content_layout.addWidget(folder_frame)
        
        # 진행바
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        content_layout.addWidget(self.progress_bar)
        
        # 변환 버튼
        self.convert_btn = CuteButton('✨ 변환 시작 ✨')
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)
        content_layout.addWidget(self.convert_btn)
        
        layout.addWidget(content_frame)
        
        # 크레딧
        credit_label = QLabel('Made with 💖')
        credit_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(credit_label)
        
        self.selected_dir = None
        self.worker = None
        
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '폴더 선택')
        if folder:
            self.selected_dir = folder
            self.path_label.setText(f'선택된 폴더: {folder} 📂')
            self.convert_btn.setEnabled(True)
            
    def start_conversion(self):
        if not self.selected_dir:
            QMessageBox.warning(self, '알림 🔔', '폴더를 선택해주세요!')
            return
            
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        
        self.worker = ConversionWorker(self.selected_dir)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.error.connect(self.show_error)
        self.worker.start()
        
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
    def conversion_finished(self):
        QMessageBox.information(self, '완료 🎉', '모든 파일이 성공적으로 변환되었어요! ✨')
        self.convert_btn.setEnabled(True)
        
    def show_error(self, message):
        QMessageBox.critical(self, '오류 😢', message)
        self.convert_btn.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 