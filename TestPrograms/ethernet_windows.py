import socket
import struct
import time

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("", 5000))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            power = 32767
            data = [32, power >> 8 & 0xff, power & 0xff]
            data_bytes = struct.pack("{}B".format(len(data)), *data)
            print(f"data: {data_bytes}")
            conn.sendall(data_bytes)

            time.sleep(1)