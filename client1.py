from PyQt5 import QtCore, QtGui, QtWidgets
from socket import *
import sys
import os
from functools import partial
import threading
import time

istemci = socket(AF_INET, SOCK_DGRAM)
host = '172.20.10.2'
port = 12345

class WorkerThread(QtCore.QThread):
    messageReceived = QtCore.pyqtSignal(str)  

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            mesaj, adres = istemci.recvfrom(4096)
            mesaj = mesaj.decode()
            self.messageReceived.emit(mesaj)

class Ui_Dialog(QtWidgets.QDialog):

    def __init__(self):
        super().__init__()
        self.puan = 0
        self.secmeSirasi = 0
        self.sira = False
        self.ilkKart = None
        self.ikinciKart = None
        self.secimler = ""
        self.cikanKartlar = list()
        self.cikanDegerler = list()
   
        self.workerThread = WorkerThread()
        self.workerThread.messageReceived.connect(self.mesaj_isle)

        istemci.sendto(bytes("0101", encoding="utf-8"),  (host, port))
        sonuc, adres = istemci.recvfrom(4096)
        sonuc = sonuc.decode()
        mesaj = QtWidgets.QMessageBox()
        if sonuc == "1":
            self.sira = True
            mesaj.information(self, "BAŞLAMA", "Oyuna Oyuncu 1 Başlayacak")
        else:
            mesaj.information(self, "BAŞLAMA", "Oyuna Oyuncu 2 Başlayacak")
    
    def mesaj_isle(self, mesaj):
        if "." in mesaj and mesaj.startswith("x") == True:
            sonHal = mesaj.split(".")
            if len(sonHal) == 3:
                kartNumarasi = sonHal[1]
                icindekiDeger = sonHal[2]
                for kart in self.kartlar:
                    y = kart.objectName().split("t")[1]
                    if kartNumarasi == y:
                        kart.setText(icindekiDeger)
                        font = QtGui.QFont()
                        font.setPointSize(12)
                        kart.setFont(font)
            print(mesaj)

        elif "." in mesaj and mesaj.startswith("y") == True: 
            sonHal = mesaj.split(".")
            if len(sonHal) == 6:
                oyuncuPuan = sonHal[1]
                self.oyuncu2Puan.setText(str(oyuncuPuan))
                kartNo1 = sonHal[2]
                kartNo2 = sonHal[3]
                deger1 =  sonHal[4]
                deger2 = sonHal[5]
                xKart = "kart" + kartNo1
                yKart = "kart" + kartNo2
                for kart in self.kartlar:
                    y = kart.objectName().split("t")[1]
                    if kartNo2 == y:
                        kart.setText(deger2)
                        font = QtGui.QFont()
                        font.setPointSize(12)
                        kart.setFont(font)
                        if deger1 == deger2 and yKart == kart.objectName():
                            self.cikanKartlar.append(kart)
                    if kart.objectName() == xKart and deger1 == deger2:
                        self.cikanKartlar.append(kart)
                self.timer = QtCore.QTimer()
                self.timer.setSingleShot(True)
                self.timer.timeout.connect(partial(self.xMetot, deger1, deger2))
                self.timer.start(2000)
                
        elif mesaj.startswith("a") == True:
            if self.secmeSirasi % 2 == 1:
                sonHal = mesaj.split(".")
                cardNo = sonHal[1]
                value = sonHal[2]
                self.kartSecimi1(cardNo, value)
                print(mesaj)
            else:
                sonHal = mesaj.split(".")
                kart1 = sonHal[1]
                kart2 = sonHal[2]
                sayi1 = sonHal[3]
                sayi2 = sonHal[4]
                for kart in self.kartlar:
                    if kart.objectName().split("t")[1] == kart2:
                        self.ikinciKart = kart
                self.ikinciKart.setEnabled(False)
        
                if sayi1 == sayi2:
                    self.puan += 10
                    self.oyuncu1Puan.setText(str(self.puan))
                    self.cikanKartlar.append(self.ilkKart)
                    self.ilkKart.setEnabled(False)
                    self.cikanKartlar.append(self.ikinciKart)
                    self.cikanDegerler.append(sayi1)
                    font = QtGui.QFont()
                    font.setPointSize(12)
                    self.ikinciKart.setFont(font)
                    self.ikinciKart.setText(sayi2)
                    self.ilkKart = None
                    self.ikinciKart = None 
                    self.secimler = ""
                    self.secmeSirasi = 0
                else:
                    self.puan -= 5
                    self.oyuncu1Puan.setText(str(self.puan))
                    font = QtGui.QFont()
                    font.setPointSize(12)
                    self.ikinciKart.setFont(font)
                    self.ikinciKart.setText(sayi2)
                    self.timer = QtCore.QTimer()
                    self.timer.setSingleShot(True)
                    self.timer.timeout.connect(self.yMetot)
                    self.timer.start(500)

        elif mesaj.startswith("p") == True:
            sonHal = mesaj.split(".")
            oyuncu1Puan = int(sonHal[1])
            oyuncu2Puan = int(sonHal[2])
            final = "Oyun Tamamlandı.\nSizin Puanınız : " + str(oyuncu1Puan) + "\n" + "Rakibin Puanı : " + str(oyuncu2Puan)
            if oyuncu1Puan > oyuncu2Puan:
                final = final + "\nKazanan Siz Oldunuz."
            elif oyuncu1Puan == oyuncu2Puan:
                final = final + "\nBerabere Bitti."
            else:
                final = final + "\nRakibiniz Kazandı."
            mesajKutusu = QtWidgets.QMessageBox()
            mesajKutusu.information(Dialog, "SONUÇ", final)  
        
        elif mesaj == "yeniden":
            mesaj = QtWidgets.QMessageBox()
            sonuc = mesaj.question(Dialog, "TALEP", "Rakibiniz oyuna yeniden başlamayı talep ediyor.\nOnaylıyor musunuz?", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if sonuc == QtWidgets.QMessageBox.Yes:
                istemci.sendto(bytes("bitir", encoding="utf-8"), (host, port))
                time.sleep(3)
                QtWidgets.QApplication.quit()
                os.execl(sys.executable, sys.executable, *sys.argv)

        elif mesaj == "bitirme_talebi":
            time.sleep(3)
            QtWidgets.QApplication.quit()
            os.execl(sys.executable, sys.executable, *sys.argv)
              
    def yMetot(self):
        self.ilkKart.setText("")
        self.ikinciKart.setText("")
        self.pasiflestirme()
        self.sira = False  
        self.ilkKart = None
        self.ikinciKart = None 
        self.secimler = ""
        self.secmeSirasi = 0

    def xMetot(self, deger1, deger2):
        if deger1 != deger2: 
            for kart in self.kartlar:
                if kart not in self.cikanKartlar:
                    kart.setEnabled(True)
                    kart.setText("")

    def kartSecimi1(self, kartNo, deger):
        for kart in self.kartlar: 
            if kartNo == kart.objectName().split("t")[1]:
                self.ilkKart = kart
        self.ilkKart.setText(deger)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.ilkKart.setFont(font)
        self.ilkKart.setEnabled(False)
    
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1275, 926)
        Dialog.setFixedSize(1275, 926)
        self.kart1 = QtWidgets.QPushButton(Dialog)
        self.kart1.setGeometry(QtCore.QRect(120, 120, 161, 281))
        self.kart1.setText("")
        self.kart1.setObjectName("kart1")
        self.kart2 = QtWidgets.QPushButton(Dialog)
        self.kart2.setGeometry(QtCore.QRect(350, 120, 161, 281))
        self.kart2.setText("")
        self.kart2.setObjectName("kart2")
        self.kart3 = QtWidgets.QPushButton(Dialog)
        self.kart3.setGeometry(QtCore.QRect(570, 120, 161, 281))
        self.kart3.setText("")
        self.kart3.setObjectName("kart3")
        self.kart4 = QtWidgets.QPushButton(Dialog)
        self.kart4.setGeometry(QtCore.QRect(780, 120, 161, 281))
        self.kart4.setText("")
        self.kart4.setObjectName("kart4")
        self.kart5 = QtWidgets.QPushButton(Dialog)
        self.kart5.setGeometry(QtCore.QRect(1000, 120, 161, 281))
        self.kart5.setText("")
        self.kart5.setObjectName("kart5")
        self.kart10 = QtWidgets.QPushButton(Dialog)
        self.kart10.setGeometry(QtCore.QRect(1000, 440, 161, 281))
        self.kart10.setText("")
        self.kart10.setObjectName("kart10")
        self.kart7 = QtWidgets.QPushButton(Dialog)
        self.kart7.setGeometry(QtCore.QRect(350, 440, 161, 281))
        self.kart7.setText("")
        self.kart7.setObjectName("kart7")
        self.kart6 = QtWidgets.QPushButton(Dialog)
        self.kart6.setGeometry(QtCore.QRect(120, 440, 161, 281))
        self.kart6.setText("")
        self.kart6.setObjectName("kart6")
        self.kart9 = QtWidgets.QPushButton(Dialog)
        self.kart9.setGeometry(QtCore.QRect(780, 440, 161, 281))
        self.kart9.setText("")
        self.kart9.setObjectName("kart9")
        self.kart8 = QtWidgets.QPushButton(Dialog)
        self.kart8.setGeometry(QtCore.QRect(570, 440, 161, 281))
        self.kart8.setText("")
        self.kart8.setObjectName("kart8")
        self.yenidenBasla = QtWidgets.QPushButton(Dialog)
        self.yenidenBasla.setGeometry(QtCore.QRect(520, 800, 261, 61))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.yenidenBasla.setFont(font)
        self.yenidenBasla.setStyleSheet("background-color: lightblue;\n"
"color: white;")
        self.yenidenBasla.setObjectName("yenidenBasla")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(130, 40, 81, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.oyuncu1Puan = QtWidgets.QLabel(Dialog)
        self.oyuncu1Puan.setGeometry(QtCore.QRect(230, 43, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.oyuncu1Puan.setFont(font)
        self.oyuncu1Puan.setObjectName("oyuncu1Puan")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(1000, 40, 81, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.oyuncu2Puan = QtWidgets.QLabel(Dialog)
        self.oyuncu2Puan.setGeometry(QtCore.QRect(1090, 47, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.oyuncu2Puan.setFont(font)
        self.oyuncu2Puan.setObjectName("oyuncu2Puan")

        self.yenidenBasla.clicked.connect(partial(self.kartSecme, self.yenidenBasla))

        self.kartlar = [self.kart1, self.kart2, self.kart3, self.kart4, self.kart5, self.kart6, self.kart7, self.kart8, self.kart9, self.kart10]
        for kart in self.kartlar:
            kart.clicked.connect(partial(self.kartSecme, kart))
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

        if self.sira == False:
            self.pasiflestirme()
        else:
            self.aktiflestirme()

        self.workerThread.start()

    def kartSecme(self, kart):
       threading.Thread(target=self.kartSecmeThread, args=(kart, )).start()

    def pasiflestirme(self):
        for kart in self.kartlar:
            kart.setDisabled(True)
    
    def aktiflestirme(self):
        for kart in self.kartlar:
            kart.setEnabled(True)

    def kartSecmeThread(self, kart):
        if kart.objectName() == "yenidenBasla":
            istemci.sendto(bytes("yeni", encoding="utf-8"), (host, port))
        elif self.secmeSirasi == 0:
            self.secmeSirasi += 1
            no = kart.objectName().split("t")[1]
            self.secimler = no
            istemci.sendto(bytes(self.secimler, encoding="utf-8"), (host, port))           
        elif self.secmeSirasi == 1:
            self.secmeSirasi += 1
            no = kart.objectName().split("t")[1]
            self.secimler = self.secimler + "." + no
            istemci.sendto(bytes(self.secimler, encoding="utf-8"), (host, port))

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "OYUNCU 1"))
        self.yenidenBasla.setText(_translate("Dialog", "YENİDEN BAŞLA"))
        self.label.setText(_translate("Dialog", "Oyuncu 1 : "))
        self.oyuncu1Puan.setText(_translate("Dialog", "0"))
        self.label_3.setText(_translate("Dialog", "Oyuncu 2 : "))
        self.oyuncu2Puan.setText(_translate("Dialog", "0"))

if __name__ == "__main__":   
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
