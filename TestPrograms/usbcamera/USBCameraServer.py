import socket
import struct
import threading
import queue
import numpy as np
import cv2 # pip install opencv-python

PORT = 8080

def receive_frames(client_socket, frame_queue):
    while True:
        try:
            # Receive the frame size from the client
            frame_size_data = client_socket.recv(struct.calcsize('<L'))
            if not frame_size_data:
                break
            frame_size = struct.unpack('<L', frame_size_data)[0]
            # print(f"frame_size_data: {frame_size_data}")

            # Receive the frame data from the client
            frame_data = b''
            while len(frame_data) < frame_size:
                data = client_socket.recv(frame_size - len(frame_data))
                if not data:
                    break
                frame_data += data

            # Decode the MJPEG data and convert it to a BGR image
            frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)

            # Add the frame to the queue
            frame_queue.put(frame)
        except Exception as e:
            print(f'Error: {e}')
            break

def USBCameraServer():
    
    # Create a socket and bind it to a port
    server_socket = socket.socket()
    server_socket.bind(("", PORT))
    server_socket.listen(1)

    try:
        while True:
            # Wait for a client to connect
            client_socket, client_address = server_socket.accept()

            try:
                # Create a queue to hold received frames
                frame_queue = queue.Queue()

                # Start a thread to receive and decode MJPEG frames from the client
                receive_thread = threading.Thread(target=receive_frames, args=(client_socket, frame_queue))
                receive_thread.start()

                while True:
                    try:
                        # Get the next frame from the queue
                        frame = frame_queue.get()

                        # Show the frame
                        cv2.imshow('Frame', frame)

                        k = cv2.waitKey(1)
                        if k == 27:
                            break
                    except Exception as e:
                        print(f'Error: {e}')
                        break

                # Stop the receive thread and wait for it to finish
                receive_thread.join()
            finally:
                # Close the client socket
                client_socket.close()
    finally:
        # Close the server socket and release any other resources when exiting
        server_socket.close()
        cv2.destroyAllWindows()