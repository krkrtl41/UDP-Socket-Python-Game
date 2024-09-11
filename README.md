import torch
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import shutil
import face_recognition
import os
import sqlite3
import albumentations as A
import numpy as np
from PIL import Image
import pickle
from common import create_dialog
from logging_config import setup_logging

logger = setup_logging()
logger.info(f"{__name__} modülü başlatılıyor...")
try:
    class ImageSelectionDialog(QtWidgets.QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Fotoğraf Seçimi")
            self.setGeometry(100, 100, 400, 300)

            self.layout = QtWidgets.QVBoxLayout()

            self.listWidget = QtWidgets.QListWidget()
            self.layout.addWidget(self.listWidget)

            self.addButton = QtWidgets.QPushButton("Resim Ekle")
            self.addButton.clicked.connect(self.addImage)
            self.layout.addWidget(self.addButton)

            self.removeButton = QtWidgets.QPushButton("Resim Sil")
            self.removeButton.clicked.connect(self.removeImage)
            self.layout.addWidget(self.removeButton)

            self.confirmButton = QtWidgets.QPushButton("Onayla")
            self.confirmButton.clicked.connect(self.accept)
            self.layout.addWidget(self.confirmButton)

            self.setLayout(self.layout)

            self.selected_images = []

        def addImage(self):
            files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Resim Seç", "", "Image Files (*.png *.jpg *.jpeg)")
            for file in files:
                self.listWidget.addItem(file)
                self.selected_images.append(file)

        def removeImage(self):
            current_item = self.listWidget.currentItem()
            if current_item:
                self.selected_images.remove(current_item.text())
                self.listWidget.takeItem(self.listWidget.row(current_item))

    def get_face_encoding(face_img):
        try:
            face_img = np.array(face_img)
            face_encoding = face_recognition.face_encodings(face_img)
            if len(face_encoding) == 0 or len(face_encoding) > 1:
                return None
            return face_encoding[0]
        except Exception as e:
            print(f"Error in get_face_encoding: {e}")
            return None

    def compare_face_with_known_faces(new_encoding, tolerance=0.45):
        with open('taninan_yuzler.pkl', 'rb') as f:
            known_faces = pickle.load(f)

        best_match = None
        best_similarity = 0

        for name, encoding in known_faces.items():
            face_distance = face_recognition.face_distance([encoding], new_encoding)[0]
            similarity = (1 - face_distance) * 100

            if similarity > best_similarity:
                best_match = name
                best_similarity = similarity

        if best_similarity >= (1 - tolerance) * 100:
            return best_match
        else:
            return None

    transform = A.Compose([
        A.Rotate(limit=30, p=0.5),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomBrightnessContrast(p=0.2),
        A.Blur(blur_limit=3, p=0.2),
        A.HueSaturationValue(p=0.2),
    ])

    def augment_image(image):
        image = np.array(image)
        augmented = transform(image=image)['image']
        return Image.fromarray(augmented)

    def process_single_image(image_path, augmentation_count=5):
        encodings = []
        non_aug_encodings = []
        try:
            img = Image.open(image_path).convert('RGB')

            encoding = get_face_encoding(img)
            if encoding is not None:
                encodings.append(encoding)
            else:
                encodings.append(encoding)
            non_aug_encodings = encodings.copy()

            for _ in range(augmentation_count):
                aug_img = augment_image(img)
                aug_encoding = get_face_encoding(aug_img)
                if aug_encoding is not None:
                    encodings.append(aug_encoding)

        except Exception as e:
            print(f"Error processing {image_path}: {e}")

        return non_aug_encodings, encodings

    class NoSpaceLineEdit(QtWidgets.QLineEdit):
        def keyPressEvent(self, event):
            if event.key() != QtCore.Qt.Key_Space:
                super().keyPressEvent(event)

    class Dialog(QtWidgets.QDialog):  
        def __init__(self):
            super().__init__()
            self.ui = Ui_Dialog()
            self.ui.setupUi(self)

    class Ui_Dialog(object):
        def __init__(self):
            self.image_process_thread = None
            self.known_face_encodings = None 
            self.degis = 0
            self.yollar = ['detsa.jpg', 'sinarge.jpg']

        def setupUi(self, Dialog):
            self.dialog = Dialog
            self.validator = QtGui.QIntValidator()
            self.sayac = 0
            self.adlar = list()
            self.soyadlar = list()
            self.sicilNolar = list()
            self.personelBilgiler = [self.adlar, self.soyadlar, self.sicilNolar]
            self.filePath = ""

            Dialog.setObjectName("Dialog")
            Dialog.resize(1216, 850)
            Dialog.setFixedSize(1216, 850)
            self.tabWidget = QtWidgets.QTabWidget(Dialog)
            self.tabWidget.setGeometry(QtCore.QRect(1, 0, 1221, 850))
            font = QtGui.QFont()
            font.setPointSize(10)
            self.tabWidget.setFont(font)
            self.tabWidget.setObjectName("tabWidget")

            self.tab_2 = QtWidgets.QWidget()
            self.tab_2.setObjectName("tab_2")
            self.label1000 = QtWidgets.QLabel(self.tab_2)
            self.label1000.setGeometry(QtCore.QRect(40, 730, 121, 16))
            sont = QtGui.QFont()
            sont.setPointSize(10)
            self.label1000.setFont(font)
            self.label1000.setObjectName("label1000")
            self.label1001 = QtWidgets.QLabel(self.tab_2)
            self.label1001.setGeometry(QtCore.QRect(160, 730, 191, 21))
            sont = QtGui.QFont()
            sont.setPointSize(10)
            self.label1001.setFont(font)
            self.label1001.setObjectName("label1001")
            self.pEkle = QtWidgets.QPushButton(self.tab_2)
            self.pEkle.setGeometry(QtCore.QRect(80, 590, 181, 51))
            self.pEkle.setObjectName("pEkle")
            self.pSil = QtWidgets.QPushButton(self.tab_2)
            self.pSil.setGeometry(QtCore.QRect(620, 590, 181, 51))
            self.pSil.setObjectName("pSil")
            self.pGuncelle = QtWidgets.QPushButton(self.tab_2)
            self.pGuncelle.setGeometry(QtCore.QRect(940, 590, 181, 51))
            self.pGuncelle.setObjectName("pGuncelle")
            self.label = QtWidgets.QLabel(self.tab_2)
            self.label.setGeometry(QtCore.QRect(60, 50, 71, 16))
            font = QtGui.QFont()
            font.setPointSize(12)
            self.label.setFont(font)
            self.label.setObjectName("label")
            self.label_2 = QtWidgets.QLabel(self.tab_2)
            self.label_2.setGeometry(QtCore.QRect(60, 120, 71, 16))
            font = QtGui.QFont()
            font.setPointSize(12)
            self.label_2.setFont(font)
            self.label_2.setObjectName("label_2")
            self.label_3 = QtWidgets.QLabel(self.tab_2)
            self.label_3.setGeometry(QtCore.QRect(60, 190, 71, 16))
            font = QtGui.QFont()
            font.setPointSize(12)
            self.label_3.setFont(font)
            self.label_3.setObjectName("label_3")
            self.pGoster = QtWidgets.QTableWidget(self.tab_2)
            self.pGoster.setGeometry(QtCore.QRect(530, 10, 671, 481))
            self.pGoster.setObjectName("pGoster")
            self.pGoster.setColumnCount(0)
            self.pGoster.setRowCount(0)
            self.pGoster.setStyleSheet("""
                QTableWidget {
                    background-color: #f0f0f0;  # Normal arka plan rengi
                }
                QTableWidget::item {
                    background-color: #ffffff;  # Hücrelerin arka plan rengi
                }
                QTableWidget::item:selected {
                    background-color: #cceeff;  # Seçili hücre arka plan rengi
                }
            """)
            self.pGoster.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            self.pGoster.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            self.personelAd = QtWidgets.QLineEdit(self.tab_2)
            self.personelAd.setGeometry(QtCore.QRect(180, 40, 211, 31))
            font = QtGui.QFont()
            font.setPointSize(10)
            self.personelAd.setFont(font)
            self.personelAd.setPlaceholderText("")
            self.personelAd.setObjectName("personelAd")
            self.personelSoyad = QtWidgets.QLineEdit(self.tab_2)
            self.personelSoyad.setGeometry(QtCore.QRect(180, 110, 211, 31))
            font = QtGui.QFont()
            font.setPointSize(10)
            self.personelSoyad.setFont(font)
            self.personelSoyad.setPlaceholderText("")
            self.personelSoyad.setObjectName("personelSoyad")
            self.personelSicil = QtWidgets.QLineEdit(self.tab_2)
            self.personelSicil.setGeometry(QtCore.QRect(180, 180, 211, 31))
            font = QtGui.QFont()
            font.setPointSize(10)
            self.personelSicil.setFont(font)
            self.personelSicil.setPlaceholderText("")
            self.personelSicil.setObjectName("personelSicil")
            self.personelSicil.setValidator(self.validator)
            self.label_5 = QtWidgets.QLabel(self.tab_2)
            self.label_5.setGeometry(QtCore.QRect(60, 260, 81, 41))
            font = QtGui.QFont()
            font.setPointSize(12)
            self.label_5.setFont(font)
            self.label_5.setObjectName("label_5")
            self.fotografYukle = QtWidgets.QPushButton(self.tab_2)
            self.fotografYukle.setGeometry(QtCore.QRect(390, 310, 93, 28))
            self.fotografYukle.setObjectName("fotografYukle")
            self.yKaydet_3 = QtWidgets.QPushButton(self.tab_2)
            self.yKaydet_3.setGeometry(QtCore.QRect(510, 700, 151, 51))
            self.yKaydet_3.setObjectName("yKaydet_3")
            self.label_11 = QtWidgets.QLabel(self.tab_2)
            self.label_11.setGeometry(QtCore.QRect(180, 250, 181, 171))
            self.label_11.setObjectName("label_11")
            self.label_11.setStyleSheet("border: 2px solid green")
            self.label_photo = QtWidgets.QLabel(self.tab_2)
            self.label_photo.setObjectName("label_photo")
            self.label_photo.setGeometry(QtCore.QRect(985, 720, 200, 80))  
            pixmap = QtGui.QPixmap("detsa.jpg") 
            self.label_photo.setPixmap(pixmap)
            self.label_photo.setScaledContents(True)
            self.tabWidget.addTab(self.tab_2, "")
            self.alt_yazi = QtWidgets.QLabel(self.tab_2)
            self.alt_yazi.setGeometry(QtCore.QRect(312, 760, 550, 70))  
            self.alt_yazi.setAlignment(QtCore.Qt.AlignCenter)  
            self.alt_yazi.setStyleSheet("font-size: 16px; font-family: Arial; color: black; text-decoration: none;")
            link = "<a href='https://sinarge.com.tr/'> © 2024 Sinarge Türkiye</a>"
            self.alt_yazi.setText(link)
            self.alt_yazi.setOpenExternalLinks(True)
            self.retranslateUi(Dialog)
            QtCore.QMetaObject.connectSlotsByName(Dialog)
            self.fotografYukle.clicked.connect(self.fotografYukleme)
            self.pEkle.clicked.connect(self.personelEkleme)
            self.pSil.clicked.connect(self.personelSilme)
            self.pGuncelle.clicked.connect(self.personelGuncelleme)
            self.yKaydet_3.clicked.connect(self.arayuze_git)
            self.PveritabaniGoster()

            self.timer = QtCore.QTimer(Dialog)
            self.timer.timeout.connect(self.change_image)
            self.timer.start(10000) 
            self.change_image()

        def yollariBelirt(self, url1, url2):
            self.url1 = url1
            self.url2 = url2
            print("url1 : " + url1)
            print("url2 : " + url2)

        def retranslateUi(self, Dialog):
            _translate = QtCore.QCoreApplication.translate
            Dialog.setWindowTitle(_translate("Dialog", "Personel Yönetimi"))
            self.pEkle.setText(_translate("Dialog", "PERSONEL EKLE"))
            self.pSil.setText(_translate("Dialog", "PERSONEL SİL"))
            self.pGuncelle.setText(_translate("Dialog", "PERSONEL GÜNCELLE"))
            self.label.setText(_translate("Dialog", "Adı"))
            self.label_2.setText(_translate("Dialog", "Soyadı"))
            self.label_3.setText(_translate("Dialog", "Sicil No"))
            self.label_5.setText(_translate("Dialog", "Fotoğraf"))
            self.fotografYukle.setText(_translate("Dialog", "Yükle"))
            self.yKaydet_3.setText(_translate("Dialog", "İZLEME MODU"))
            self.label_11.setText(_translate("Dialog", "Fotograf"))
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Dialog", "Personel Sayfası"))
            self.label1000.setText(_translate("Dialog", "Aktif Kullanıcı : "))
            self.label1001.setText(_translate("Dialog", "DETSA"))

        def arayuze_git(self):
            # self.dialog.close()
            # QtWidgets.QApplication.quit()
            # python_executable = sys.executable
            # script_path = "ARAYUZ2.py"
            # subprocess.Popen([python_executable, script_path])
            # sys.exit()
            
            # torch.cuda.empty_cache()
            self.dialog.close()
            from ARAYUZ2 import Ui_Dialog as Arayuz2Dialog
            self.dialog, self.ui_yonetim2 = create_dialog(Arayuz2Dialog)
            self.ui_yonetim2.yollariBelirt(self.url1, self.url2) 
            self.dialog.show()
            self.dialog.exec_()

        def fotografYukleme(self):
            dialog = ImageSelectionDialog(self.dialog)
            sayac = 0
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                selected_images = dialog.selected_images
                if not selected_images:
                    sayac += 1
                    self.sifirlama()
                    QtWidgets.QMessageBox.warning(None, "Uyarı", "Hiç resim seçilmedi.")
                    return

                self.progress_dialog = QtWidgets.QProgressDialog("Yüzler işleniyor. Lütfen bekleyiniz.", None, 0, len(selected_images), self.dialog)
                self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
                self.progress_dialog.setAutoClose(True)
                self.progress_dialog.setWindowFlags(self.progress_dialog.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
                self.progress_dialog.setWindowTitle("İşleniyor")
                self.progress_dialog.show()

                all_encodings = []
                non_aug_encodings = []
                for i, image_path in enumerate(selected_images):
                    non_aug, encodings = process_single_image(image_path)
                    if encodings:
                        all_encodings.extend(encodings)
                        non_aug_encodings.extend(non_aug)
                        print(non_aug)
                        print(type(non_aug))
                    if all(enc is None for enc in non_aug):
                        self.progress_dialog.close() 
                        self.sifirlama()
                        sayac += 1
                        QtWidgets.QMessageBox.warning(None, "Uyarı", "Hiçbir yüz tespit edilemedi veya birden fazla yüz var.")
                        return
                    self.progress_dialog.setValue(i + 1)
                self.progress_dialog.close()
                self.progress_dialog.cancel()
                if not all_encodings:
                    self.sifirlama()
                    sayac += 1
                    QtWidgets.QMessageBox.warning(None, "Uyarı", "Hiçbir yüz tespit edilemedi veya birden fazla yüz var.")
                    return

                print("Toplam Encod Adet : " + str(len(non_aug_encodings)))
                if len(all_encodings) > 1:
                    matches = face_recognition.compare_faces(non_aug_encodings[1:], non_aug_encodings[0], tolerance=0.475)
                    mesafeler = face_recognition.face_distance(non_aug_encodings[1:], non_aug_encodings[0])
                    benzerlikler = (1 - mesafeler) * 100
                    for i, benzerlik in enumerate(benzerlikler, start=1):
                        print(f"İlk resim ile {i+1}. resim arasındaki benzerlik: {benzerlik:.2f}%")
                    if not all(matches):
                        self.sifirlama()
                        sayac += 1
                        QtWidgets.QMessageBox.warning(None, "Uyarı", "Seçilen fotoğraflardaki yüzler aynı kişiye ait değil.")
                        return

                average_encoding = np.mean(all_encodings, axis=0)

                matched_name = compare_face_with_known_faces(average_encoding)
                if matched_name:
                    self.sifirlama()
                    sayac += 1
                    QtWidgets.QMessageBox.warning(None, "Uyarı", f"Bu yüz zaten {matched_name} olarak kaydedilmiş.")
                    return
                self.progress_dialog.close()

                if sayac == 0:
                    self.selected_images = selected_images
                    self.average_encoding = average_encoding
                    self.filePath = selected_images[0]
                    self.display_image(selected_images[0]) 

        def sifirlama(self):
            self.selected_images = []
            self.average_encoding = None
            self.filePath = None
            self.label_11.clear()

        def change_image(self):
            self.degis = (self.degis + 1) % len(self.yollar)
            next_pixmap = QtGui.QPixmap(self.yollar[self.degis])

            self.opacity_effect = QtWidgets.QGraphicsOpacityEffect()
            self.label_photo.setGraphicsEffect(self.opacity_effect)
            self.animation = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
            self.animation.setDuration(1500)
            self.animation.setStartValue(1.0)
            self.animation.setEndValue(0.0)
            self.animation.finished.connect(lambda: self.update_image(next_pixmap))
            self.animation.start()

        def update_image(self, pixmap):
            self.label_photo.setPixmap(pixmap)

            self.animation = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
            self.animation.setDuration(1000)
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()

        def personelEkleme(self):
            if self.personelAd.text().strip() == "" or self.personelSoyad.text().strip() == "" or not hasattr(self, 'selected_images') or self.personelSicil.text().strip() == "" or self.filePath == None:
                QtWidgets.QMessageBox.warning(None, "HATA", "Lütfen tüm alanları doğru ve eksiksiz bir şekilde doldurun.")
            elif int(self.personelSicil.text().strip()) in self.sicilNolar:
                QtWidgets.QMessageBox.warning(None, "HATA", "Bu sicil no kullanılmaktadır.")
            else:
                ad_clean = self.turkish_char_replace(self.personelAd.text().strip())
                soyad_clean = self.turkish_char_replace(self.personelSoyad.text().strip())
                hedef_klasor = os.path.join("resimler", ad_clean + " " + soyad_clean)
                os.makedirs(hedef_klasor)

                for i, image_path in enumerate(self.selected_images):
                    _, ext = os.path.splitext(image_path)
                    hedef_yol = os.path.join(hedef_klasor, f"{ad_clean}_{soyad_clean}_{i}{ext}")
                    shutil.copy2(image_path, hedef_yol)

                connection = sqlite3.connect("sinarge.db")
                cursor = connection.cursor()
                sorgu = "INSERT INTO Personeller VALUES (?, ?, ?, 0, 0, 0)"
                cursor.execute(sorgu, (ad_clean, soyad_clean, int(self.personelSicil.text().strip())))
                connection.commit()
                cursor.close()
                connection.close()

                pickle_yuzler = None
                with open('taninan_yuzler.pkl', 'rb') as f:
                    pickle_yuzler = pickle.load(f)

                isim_soy = ad_clean + " " + soyad_clean
                pickle_yuzler[isim_soy] = self.average_encoding

                with open('taninan_yuzler.pkl', 'wb') as f:
                    pickle.dump(pickle_yuzler, f)

                for dizi in self.personelBilgiler:
                    dizi.clear()

                self.personelAd.clear()
                self.personelSoyad.clear()
                self.personelSicil.clear()
                self.label_11.clear()
                self.selected_images = []
                self.average_encoding = None
                self.filePath = None
                pickle_yuzler = None
                self.PveritabaniGoster()
                QtWidgets.QMessageBox.information(None, "Bilgi", "Personel başarıyla eklendi.")
                self.pGoster.clearSelection()

        def display_image(self, file_path):
            pixmap = QtGui.QPixmap(file_path)
            self.label_11.setPixmap(pixmap.scaled(self.label_11.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            self.sayac += 1
            self.filePath = file_path

        def PveritabaniGoster(self):
            connection = sqlite3.connect("sinarge.db")
            cursor = connection.cursor()

            self.pGoster.clearContents() 
            self.adlar.clear()
            self.soyadlar.clear()
            self.sicilNolar.clear()

            cursor.execute("SELECT ad, soyad, sicilNo FROM Personeller")
            rows = cursor.fetchall()
            print("Rows fetched from DB:", rows) 

            if rows:
                columns = [description[0] for description in cursor.description]
                self.pGoster.setColumnCount(len(columns))
                self.pGoster.setHorizontalHeaderLabels(columns)

                self.pGoster.setRowCount(len(rows))

                for row_idx, row in enumerate(rows):
                    for col_idx, value in enumerate(row):
                        self.pGoster.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(value)))
                        if columns[col_idx].lower() == 'ad':
                            self.adlar.append(value)
                        elif columns[col_idx].lower() == 'soyad':
                            self.soyadlar.append(value)
                        elif columns[col_idx].lower() == "sicilno":
                            self.sicilNolar.append(value)

            cursor.close()
            connection.close()

            self.personelBilgiler = [self.adlar, self.soyadlar, self.sicilNolar]

        def turkish_char_replace(self, text):
            replacements = {
                'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
                'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
            }
            for turkish_char, replacement in replacements.items():
                text = text.replace(turkish_char, replacement)
            return text

        def personelSilme(self):
            try:
                selected_rows = set(item.row() for item in self.pGoster.selectedItems())

                if not selected_rows:
                    QtWidgets.QMessageBox.warning(None, "HATA", "Sileceğiniz kişiyi seçmeniz gerekmektedir.")
                    return

                sonuc = QtWidgets.QMessageBox.question(None, "Silme", "Kişi silinecek. Onaylıyor musunuz?")
                if sonuc != QtWidgets.QMessageBox.Yes:
                    return

                selected_row = list(selected_rows)[0]
                name = self.pGoster.item(selected_row, 0).text()
                surname = self.pGoster.item(selected_row, 1).text()
                _sicil = self.pGoster.item(selected_row, 2).text()

                connection = sqlite3.connect("sinarge.db")
                cursor = connection.cursor()
                try:
                    sorgu = "DELETE FROM Personeller WHERE sicilNo = ?"
                    cursor.execute(sorgu, (int(_sicil),))
                    connection.commit()
                except sqlite3.Error as e:
                    QtWidgets.QMessageBox.critical(None, "Veritabanı Hatası", f"Silme işlemi sırasında bir hata oluştu: {e}")
                    return
                finally:
                    cursor.close()
                    connection.close()

                for dizi in self.personelBilgiler:
                    dizi.clear()

                known_faces = None
                with open("taninan_yuzler.pkl", "rb") as f:
                    known_faces = pickle.load(f)
                info = name + " " + surname
                if info in known_faces:
                    del known_faces[info]

                with open("taninan_yuzler.pkl", "wb") as f:
                    pickle.dump(known_faces, f)

                known_faces = None

                klasor_yolu = os.path.join("resimler", f"{name} {surname}")
                if os.path.exists(klasor_yolu):
                    try:
                        shutil.rmtree(klasor_yolu)
                    except PermissionError:
                        QtWidgets.QMessageBox.warning(None, "Uyarı", f"{klasor_yolu} klasörü silinemedi. Dosya kullanımda olabilir.")
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(None, "Uyarı", f"Klasör silme sırasında bir hata oluştu: {e}")
                else:
                    print(f"Uyarı: {klasor_yolu} klasörü bulunamadı.")
                    # logger.debug(f"Uyarı: {klasor_yolu} klasörü bulunamadı.")

                self.PveritabaniGoster()
                QtWidgets.QMessageBox.information(None, "Bilgi", "Personel başarıyla silindi.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(None, "Hata", f"Beklenmeyen bir hata oluştu: {e}")
            finally:
                self.pGoster.clearSelection()

        def personelGuncelleme(self):
            bolumler = [self.personelAd, self.personelSoyad, self.personelSicil]
            girilenler = [bolum for bolum in bolumler if bolum.text().strip() != ""]
            kacTaneGirdi = len(girilenler)
            selected_rows = set(item.row() for item in self.pGoster.selectedItems())
            satirAdet = len(selected_rows)
            if satirAdet == 0 or kacTaneGirdi == 0:
                QtWidgets.QMessageBox.warning(None, "HATA", "Güncelleyeceğiniz kişiyi seçmeniz ve güncellenecek bilgiyi girmeniz gerekmektedir.")
                return

            selected_row = list(selected_rows)[0]
            name = self.pGoster.item(selected_row, 0).text()
            surname = self.pGoster.item(selected_row, 1).text()
            _sicil = int(self.pGoster.item(selected_row, 2).text())

            dosya_adi = f"resimler\\{name} {surname}"
            newName, newSurname = name, surname
            try:
                if self.personelSicil in girilenler:
                    connection2 = sqlite3.connect("sinarge.db")
                    cursor2 = connection2.cursor()
                    cursor2.execute("SELECT sicilNo FROM Personeller WHERE sicilNo != ?", (_sicil, ))
                    dizi = [row[0] for row in cursor2.fetchall()]
                    new_sicil = int(self.personelSicil.text().strip())
                    if new_sicil in dizi or _sicil == new_sicil:
                        connection2.commit()
                        cursor2.close()
                        connection2.close()
                        QtWidgets.QMessageBox.warning(None, "HATA", "Bu sicil numarası kullanılmaktadır ya da kişi bu sicil numarasına sahip.")
                    else:
                        connection = sqlite3.connect("sinarge.db")
                        cursor = connection.cursor()
                        cursor.execute("UPDATE Personeller SET sicilNo = ? WHERE sicilNo = ?", (new_sicil, _sicil))
                        _sicil = new_sicil  
                        connection.commit()
                        cursor.close()
                        connection.close()
                else:
                    connection = sqlite3.connect("sinarge.db")
                    cursor = connection.cursor()
                    updates = []
                    params = []
                    girme = 0
                    if self.personelAd in girilenler:
                        newName = self.turkish_char_replace(self.personelAd.text().strip())
                        updates.append("ad = ?")
                        params.append(newName)
                        girme += 1
                    if self.personelSoyad in girilenler:
                        newSurname = self.turkish_char_replace(self.personelSoyad.text().strip())
                        updates.append("soyad = ?")
                        params.append(newSurname)
                        girme += 1
                    if updates:
                        query = f"UPDATE Personeller SET {', '.join(updates)} WHERE sicilNo = ?"
                        params.append(_sicil)
                        cursor.execute(query, params)
                        connection.commit()
                        cursor.close()
                        connection.close()

                    os.rename(dosya_adi, f"resimler\\{newName} {newSurname}")

                    if girme != 0:
                        bilinen_yuzler = None
                        degisecek_yer = ""

                        with open("taninan_yuzler.pkl", "rb") as f:
                            bilinen_yuzler = pickle.load(f)

                        anahtar = newName + " " + newSurname
                        for key in bilinen_yuzler.keys():
                            if name + " " + surname == key:
                               degisecek_yer = key
                               break
                        bilinen_yuzler[anahtar] = bilinen_yuzler.pop(degisecek_yer)
                        with open("taninan_yuzler.pkl", "wb") as f:
                            pickle.dump(bilinen_yuzler, f)

                    girme = 0
                    for widget in bolumler:
                        widget.clear()
                    self.label_11.clear()
                    self.filePath = ""
                self.personelSicil.clear()
                self.PveritabaniGoster()
            except Exception as e:
                print(e)

    if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        dialog = Dialog()
        dialog.show()
        sys.exit(app.exec_())

except Exception as e:
    logger.error(f"Hata oluştu : {e}")
