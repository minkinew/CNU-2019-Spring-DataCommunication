import socket 
import os
import struct
import time as t
import sys

def checksum(s, checksum):
    sum = 0
    for i in range(len(s)):
        sum = sum + s[i]
    temp = sum >> 16
    chk = sum + temp + checksum # byte형 
    
    if chk >= 131072 : # 131072는 이진수로 17비트
        chk = chk - 131072
    if chk >= 65536 : # 65536는 이진수로 18비트
        chk = chk - 65536
        
    chk = chk ^ 0xffff # 보수를 취함
    return chk

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # socket 객체 생성(UDP)
s.bind(('',4200))

current_length = 0
p_SequenceNumber = "0"
ACK = "1"

header_result, addr = s.recvfrom(1080) 

print("Reciver Socket Open...")
print("Sender IP : ", addr[0] )
print("Sender Port : ",addr[1] )

file_type = chr(header_result[0]) # 헤더의 파일 타입
header_checksum = int.from_bytes(header_result[1:21],byteorder = "big") # 체크썸 20바이트 bigEndian
total_size = int.from_bytes(header_result[21:41], byteorder = "big") # 헤더의 파일의 크기 20바이트 bigEndian
file_name = header_result[41:56] # 헤더의 파일 이름 15바이트 
file_name = file_name[0:file_name.find(32)].decode() # 뒤에 쓰레기 값 
header_data = header_result[56:] # 헤더의 payload

print("File Name = ", file_name)
print("File Size = ", total_size)

frame_result = file_type.encode() + total_size.to_bytes(20, byteorder = "big") + file_name.encode().ljust(15) + header_data # 1060바이트 encode 
check = checksum(frame_result, header_checksum) # 체크썸 

while 1 :
    if check == 0: # 체크썸이 맞으면 받음 
        with open(file_name, 'wb') as f : # 쓰기 전용, 이진 모드로 파일 열기
            f.write(header_data) # 파일의 내용을 씀
            current_length = current_length + 1024 # current_length 1024씩 증가 
            percent = current_length / total_size * 100
            if(current_length >= total_size):
                current_length = total_size
                percent = 100.0
            print("current_size / total_size : " , current_length, "/" , total_size , percent,"%")
            if(percent == 100.0):
                print("File recive End")

            s.sendto(ACK.encode(), addr)

            while 1 :
                payload_result, addr = s.recvfrom(1080)
                payload_type = chr(payload_result[0]) # 페이로드의 파일 타입
                payload_checksum = int.from_bytes(payload_result[1:21], byteorder = "big") # 체크썸 20바이트 bigEndian
                payload_current_length = int.from_bytes(payload_result[21:41], byteorder = "big") # 페이로드의 current_legnth 20바이트 bigEndian
                payload_SequenceNumber = payload_result[41:56] # 페이로드의 SequenceNumber 15바이트 
                payload_SequenceNumber = payload_SequenceNumber[0:payload_SequenceNumber.find(32)].decode() # 뒤에 쓰레기 값 
                payload_data = payload_result[56:] # 페이로드의 payload

                frame_result = payload_type.encode() + payload_current_length.to_bytes(20,byteorder = "big") + payload_SequenceNumber.encode().ljust(15) + payload_data # 1060바이트 encode
                check = checksum(frame_result, payload_checksum) #체크썸 

                
                if check != 0 : # 체크썸이 다를때는 안받음 
                    ACK = "NAK2" #프레임 손상인 경우. 수신측에서 버림
                    s.sendto(ACK.encode(), addr)
                    continue

                else:
                    if payload_SequenceNumber != p_SequenceNumber:
                        f.write(payload_data)
                        percent = payload_current_length / total_size * 100
                        if payload_current_length >= total_size :
                            payload_current_legnth = total_size
                            percent = 100.0
                        print("current_size / total_size : " , payload_current_length, "/" , total_size , percent,"%")
                        if percent == 100.0:
                            print("File recive end")
                        p_SequenceNumber = payload_SequenceNumber
                        
                        if payload_SequenceNumber == "1" : # 1을 받으면 ACK 0을 보냄 
                            ACK = "0"
                            s.sendto(ACK.encode(), addr)
                            continue

                        if payload_SequenceNumber == "0": # 0을 받으면 ACK 1을 보냄 
                            ACK = "1"
                            s.sendto(ACK.encode(), addr)
                            continue
                    else:
                        ACK = "NAK1" # 순서가 바뀌는 경우. 수신측에서 버림 
                        s.sendto(ACK.encode(), addr)
                        continue
                    
    else:
        ACK = "NAK2" #프레임 손상인 경우. 수신측에서 버림
        s.sendto(ACK.encode(), addr)
        continue






