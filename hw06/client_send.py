import socket
import os

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # socket 객체 생성(UDP)
host= '192.168.137.151' # host주소
port = 8000 # port번호

filename = input("Input your file name : ") # 파일 이름을 입력
total_size = os.path.getsize(filename) # 파일의 총 크기
current_size = 0  # 파일을 보내기 전에는 데이터의 크기가 0

s.sendto(filename.encode(), (host,int(port))) # 파일이름을 인코드해서 server로 보냄
s.sendto((str(total_size)).encode(), (host,int(port))) # 파일의 총 크기를 인코드해서 server로 보냄 
print("File Transmit Start....")

with open(filename, 'rb') as f : # 읽기 전용, 이진모드로 파일 열기
    while 1 :
        data = f.read(1024) # 파일을 1024바이트씩 읽음
        current_size += 1024 # current_size 크기 1024씩 증
        s.sendto(data, (host, int(port))) # 파일을 server로 보냄
        percent = current_size / total_size * 100 # 퍼센트
 
        if current_size >= total_size: # 파일을 다 받았으면 종료
            current_size = total_size
            percent = 100
            break

        print("current_size / total_size = ", current_size, "/", total_size, percent, "%")  
        
print("current_size / total_size = ", current_size, "/", total_size, percent, "%")  
        
print("ok")
print("file_send_end")
s.close()
