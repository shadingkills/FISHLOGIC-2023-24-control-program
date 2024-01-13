import socket
import subprocess

server_socket = socket.socket()
server_socket.bind(('', 8000))
server_socket.listen()

# Accept a single connection and make a file-like object out of it
connection, addr = server_socket.accept()

print(f"connected to {addr}")

connection = connection.makefile('rb')

try:
    # Run a viewer with an appropriate command line. Uncomment the mplayer
    # version if you would prefer to use mplayer instead of VLC
    cmdline = ['vlc', '--demux', 'h264', '-']
    #cmdline = ['mplayer', '-fps', '25', '-cache', '1024', '-']
    player = subprocess.Popen(cmdline, stdin=subprocess.PIPE)
    while True:
        # Repeatedly read 1k of data from the connection and write it to
        # the media player's stdin
        data = connection.read(1024)
        if not data:
            break
        player.stdin.write(data)
finally:
    connection.close()
    server_socket.close()
    player.terminate()