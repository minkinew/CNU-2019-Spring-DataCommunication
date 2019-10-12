import socket 
import os
import struct

def checksum(s):
    sum = 0
    for i in range(len(s)):
        sum = sum + s[i]

    temp = sum >> 16
    chk = sum + temp
    
    if chk >= 131072 : # 131072이 이진수로 18비트
        chk = chk - 131072
    if chk >= 65536 : # 65536가 이진수로 17비트
        chk = chk - 65536
        
    chk = chk ^ 0xffff # 1의 보수를 취함
    return chk

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # socket 객체 생성(UDP)

s.bind(('', 4200))
s.settimeout(4)

host = '192.168.100.152' # host주소
port = 4200 # port 번호

print("Sender Socket open...")
print("Receiver IP : ", host)
print("Receiver Port : ", port)
file_name = input("Input File name : ") # 파일의 이름

file_type = "s" # 파일의 타입 s
current_length = 0 # 파일의 길이 
total_size = os.path.getsize(file_name) # 파일의 총 크기 
r_total_size = total_size.to_bytes(20, byteorder = "big") # bigEndian
r_file_name = file_name.encode().ljust(15) # 파일 이름(15) encode
SequenceNumber = "1" # 처음에 1로 시작 

with open(file_name, 'rb') as f: # 읽기 전용, 이진 모드로 파일 열기
    data = f.read(1024) # 파일을 1024바이트 읽음

    header_result = file_type.encode() + r_total_size + r_file_name + data # 1060바이트 encode 
    header_checksum = checksum(header_result).to_bytes(20, byteorder = "big") # 체크썸 20바이트
    header_result = file_type.encode() + header_checksum + r_total_size + r_file_name + data # 1080바이트 encode
    s.sendto(header_result, (host, port)) # server로 보냄
    print("Send File Info(file_Type, Checksum, file Name, file Size, Payload ) to Server...")

    while 1: # 처음에 ACK를 못받는 경우 처리
        try:    
            ACK, _ = s.recvfrom(1080)
            break
        except socket.timeout: # timeout이 나면 재전송 
            print("* TimeOut!! ***")
            print("Retransmission")
            s.sendto(header_result, (host, port)) # 1080바이트 재전송
            percent = current_length / total_size * 100
            if current_length >= total_size:
               current_length = total_size
               percent = 100.0
            print("current_size / total_size : " , current_length, "/" , total_size , percent, "%")

            s.settimeout(4) # 4초 기다림 
            continue

    if ACK.decode() == "1": #  파일전송 시작
        print("Start File Send")
        current_length = current_length + 1024
        percent = current_length / total_size * 100
        if current_length >= total_size :
           current_legnth = total_size
           percent = 100.0
        print("current_size / total_size : " , current_length, "/" , total_size , percent,"%")
    
    while 1:
        file_type = "d" # 파일의 타입 d
        current_length = + current_length + 1024
        r_current_length = current_length.to_bytes(20, byteorder = "big") # bigEndian
        r_SequenceNumber = SequenceNumber.encode().ljust(15) # SequenceNumber(15)
        data = f.read(1024) # 파일을 1024바이트 읽음 

        payload_result = file_type.encode() + r_current_length + r_SequenceNumber + data # 1060바이트 encode
        payload_checksum = checksum(payload_result).to_bytes(20, byteorder = "big") # 체크썸 20바이트
        payload_result = file_type.encode() + payload_checksum + r_current_length + r_SequenceNumber + data # 1080바이트 encode 
        s.sendto(payload_result, (host, port)) # server로 보냄

        if current_length >= total_size: # 파일 전송 완료
            percent = current_length / total_size * 100
            if current_length >= total_size :
               current_length = total_size
               percent = 100.0
            print("current_size / total_size : " , current_length, "/" , total_size , percent,"%")
            print("File send end")
            break


        try:
            ACK,_ = s.recvfrom(1080)
            percent = current_length / total_size * 100
            if ACK.decode() == "0" : # ACK가 0일 때 
                if current_length >= total_size:
                    current_legnth = total_size
                    percent = 100.0
                print("current_size / total_size : " , current_length, "/" , total_size , percent, "%")
                SequenceNumber = "0"
                continue

            elif ACK.decode() == "1": # ACK가 1일 때 
                if current_length >= total_size:
                    current_legnth = total_size
                    percent = 100.0
                print("current_size / total_size : " , current_length, "/" , total_size , percent, "%")
                SequenceNumber = "1"
                continue

            elif ACK.decode() == "NAK1" : # 순서가 바뀌는 경우. 수신측에서 버림 
                print("* Received NAK1")
                s.sendto(payload_result, (host, port))
                if current_length >= total_size:
                    current_legnth = total_size
                    percent = 100.0
                print("current_size / total_size : " , current_length, "/" , total_size , percent, "%")
                continue

            elif(ACK.decode() == "NAK2"): #프레임 손상인 경우. 수신측에서 버림
                print("* Received NAK2")
                s.sendto(payload_result, (host, port))
                if current_length >= total_size:
                    current_length = total_size
                    percent = 100.0
                print("current_size / total_size : " , current_length, "/" , total_size , percent, "%")
                continue
                
        except socket.timeout: # timeout이 나면 재전송 
            print("* TimeOut!! ***")
            print("Retransmission")
            s.sendto(payload_result, (host, port))
            percent = current_length / total_size * 100
            if current_length >= total_size:
                    current_legnth = total_size
                    percent = 100.0
            print("current_size / total_size : " , current_length, "/" , total_size , percent, "%")
            s.settimeout(4)
            continue                
