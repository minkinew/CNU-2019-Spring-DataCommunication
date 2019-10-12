import socket
import os

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # socket 객체 생성(UDP)
s.bind(('', 8000))

info, addr = s.recvfrom(3000) # 파일이름과 ip주소를 받음
t_size, _  = s.recvfrom(3000) # 파일크기만 받음
current_size = 0  # 파일을 받기 전에는 데이터의 크기가 0

print("file recv start from", addr[0])
print("File Name : ", info.decode())
print("File Size : ", t_size.decode())

with open(info, 'wb') as f : # 쓰기 전용, 이진모드로 파일 열기
    while 1 :
        data, _  = s.recvfrom(1024) # 파일의 내용을 1024바이트 만큼 받음
        f.write(data) # 파일의 내용을 디코드해서 씀
        current_size += 1024 # 파일을 1024바이트씩 반복해서 받음
        percent =  current_size / int(t_size) * 100 # 퍼센트

        
        if (current_size >= int(t_size)): # 파일을 다 받았으면 종료
            current_size = t_size
            percent = 100
            break
        
        print("current_size / total_size = ", current_size, "/", t_size.decode(), percent, "%")  
        
print("current_size / total_size = ", current_size.decode(), "/", t_size.decode(), percent, "%")  
        
s.close()
