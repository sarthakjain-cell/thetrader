import socket

def check_port(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

is_open = check_port('206.189.129.232', 8501)
print(f"Port 8501 Open: {is_open}")
