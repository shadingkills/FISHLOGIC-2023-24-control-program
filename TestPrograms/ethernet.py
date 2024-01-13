import socket
import time

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    # Send a message to the Raspberry Pi 4
    message = b'Hello, Raspberry Pi 4!'
    sent_time = time.time()
    sock.sendto(message, ('127.0.1.1', 100))
    print("sent")

    # Wait for a response from the Raspberry Pi 4
    data, server = sock.recvfrom(4096)
    received_time = time.time()

    # Calculate and print the latency
    latency = received_time - sent_time
    print('Latency:', latency)
