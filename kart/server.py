import socket
import random
import sys
import os
import time

PORT = 12345
n = 0
baslama = 0
sira = 0
kartAdedi = 0

client_address1 = ""
client_address2 = ""

kartlar = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
degerler = [100, 100, 200, 200, 300, 300, 400, 400, 500, 500]
eslesmeler = [-1] * 10
degerlerSonHal = [0] * 10
istemciler = []

oyuncu1Puan = 0
oyuncu2Puan = 0
random.seed()
for i in range(len(kartlar)):
    while True:
        random_index = random.randint(0, 9)
        if eslesmeler[random_index] == -1:
            eslesmeler[random_index] = kartlar[i]
            degerlerSonHal[i] = degerler[random_index]
            break

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('172.20.10.2', PORT))

print("Sunucu başlatıldı. Port:", PORT)

while True:
    deger, client_address = server_socket.recvfrom(4096)
    deger = deger.decode()

    x = 0

    if deger == "0101":
        print("Mesaj 1:", deger)
        client_address1 = client_address
        if baslama == 0:
            random_number = random.randint(1, 2)
            sira = str(random_number)
            print("Client1 : " + str(client_address1[0]) + ", " + str(client_address1[1]))
        
        server_socket.sendto(sira.encode(), client_address)
        print("Sıra:", sira)
        print("Kartlar:", " - ".join(map(str, degerlerSonHal)))
        baslama += 1

    elif deger == "1010":
        print("Mesaj 2:", deger)
        client_address2 = client_address
        if baslama == 0:
            print("Mesaj 1:", deger)
            random_number = random.randint(1, 2)
            sira = str(random_number)
            
        print("Client2 : " + str(client_address2[0]) + ", " + str(client_address2[1])) 
        server_socket.sendto(sira.encode(), client_address)
        print("Sıra:", sira)
        print("Kartlar:", " - ".join(map(str, degerlerSonHal)))
        baslama += 1

    elif deger == "yeni":
        if client_address == client_address1:
            server_socket.sendto(bytes("yeniden", encoding="utf-8"), client_address2)
        else:
            server_socket.sendto(bytes("yeniden", encoding="utf-8"), client_address1)
    
    elif deger == "bitir":
        if client_address == client_address1:
            server_socket.sendto(bytes("bitirme_talebi", encoding="utf-8"), client_address2)
        else:
            server_socket.sendto(bytes("bitirme_talebi", encoding="utf-8"), client_address1) 
        time.sleep(0.2)
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    else:
        print("Client1 : " + str(client_address1[0]) + ", " + str(client_address1[1]) + ", Client2 : " + str(client_address2[0]) + ", " + str(client_address2[1]))
        n += 1
        if n % 2 != 0:
            value = degerlerSonHal[int(deger) - 1]
            sonuc = str(value)
            anaCevap = "a." + str(deger) + "." + sonuc
            server_socket.sendto(bytes(anaCevap, encoding="utf-8"), client_address)
            cevap = "x." + str(deger) + "." + sonuc

            if(client_address == client_address1):
                server_socket.sendto(bytes(cevap, encoding="utf-8"), client_address2)
            else:
                server_socket.sendto(bytes(cevap, encoding="utf-8"), client_address1)
            print("Kart:", deger, "Değer:", value)

        else:
            deger1, deger2 = map(int, deger.split("."))
            value1 = degerlerSonHal[deger1 - 1]
            value2 = degerlerSonHal[deger2 - 1]
            sonuc = str(value1) + "." + str(value2)
            print("Sonuç:", sonuc, "Değerler:", deger)

            if sira == "1" and value1 != value2:
                oyuncu1Puan -= 5
                anaCevap = "a." + str(deger1) + "." + str(deger2) + "." + sonuc
                server_socket.sendto(bytes(anaCevap, encoding="utf-8"), client_address1)
                cevap = "y." + str(oyuncu1Puan) + "." + str(deger1) + "." + str(deger2) + "." + sonuc
                server_socket.sendto(bytes(cevap, encoding="utf-8"), client_address2)
                sira = "2"

            elif sira == "1" and value1 == value2:
                oyuncu1Puan += 10
                anaCevap = "a." + str(deger1) + "." + str(deger2) + "." + sonuc
                server_socket.sendto(bytes(anaCevap, encoding="utf-8"), client_address1)
                cevap = "y." + str(oyuncu1Puan) + "." + str(deger1) + "." + str(deger2) + "." + sonuc
                server_socket.sendto(bytes(cevap, encoding="utf-8"), client_address2)
                kartAdedi += 2
                
            elif sira == "2" and value1 != value2:
                oyuncu2Puan -= 5
                anaCevap = "a." + str(deger1) + "." + str(deger2) + "." + sonuc
                server_socket.sendto(bytes(anaCevap, encoding="utf-8"), client_address2)
                cevap = "y." + str(oyuncu2Puan) + "." + str(deger1) + "." + str(deger2) + "." + sonuc
                server_socket.sendto(bytes(cevap, encoding="utf-8"), client_address1)                
                sira = "1"
                
            elif sira == "2" and value1 == value2:
                anaCevap = "a." + str(deger1) + "." + str(deger2) + "." + sonuc
                server_socket.sendto(bytes(anaCevap, encoding="utf-8"), client_address2)
                oyuncu2Puan += 10
                cevap = "y." + str(oyuncu2Puan) + "." + str(deger1) + "." + str(deger2) + "." + sonuc
                server_socket.sendto(bytes(cevap, encoding="utf-8"), client_address1)
                kartAdedi += 2

            if kartAdedi == 10:
                son = "p." + str(oyuncu1Puan) + "." + str(oyuncu2Puan)
                server_socket.sendto(bytes(son, encoding="utf-8"), client_address1)
                server_socket.sendto(bytes(son, encoding="utf-8"), client_address2)
                oyuncu1Puan = 0
                oyuncu2Puan = 0
