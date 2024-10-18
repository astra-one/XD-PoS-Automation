import socket
import signal
import sys
class TCPClient:
    def __init__(self, source_ip="127.0.0.1", target_ip="192.168.15.100", target_port=8978):
        self.source_ip = source_ip
        self.target_ip = target_ip
        self.target_port = target_port
        self.client_socket = None

    def connect(self, connect_timeout=None, read_timeout=None):
        """Establish the TCP connection (SYN process)."""
        try:
            self.client_socket = self.create_socket(connect_timeout)
            self.client_socket.connect((self.target_ip, self.target_port))
            self.set_read_timeout(read_timeout)
        except Exception as e:
            print(f"[Client] Connection error: {e}")
            self.client_socket = None

    def create_socket(self, connect_timeout=None):
        """Create a TCP socket and configure connection timeout."""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if connect_timeout is not None:
            client_socket.settimeout(connect_timeout)
        return client_socket

    def set_read_timeout(self, read_timeout=None):
        """Set a read timeout for the socket."""
        if read_timeout is not None:
            self.client_socket.settimeout(read_timeout)

    def send_data(self, message, connect_timeout=None, read_timeout=None):
        """Send ASCII-encoded message to the server."""
        if self.client_socket is None:
            print("[Client] Not connected to the server.")
            return None

        try:
            self.client_socket.sendall(message.encode("ascii"))
            return self.receive_response()
        except Exception as e:
            print(f"[Client] Error during send or receive: {e}")
        finally:
            self.close()

    def receive_response(self):
        """Receive data from the server and return the full response."""
        full_response = ""
        try:
            while True:
                response = self.client_socket.recv(1024)
                if not response:
                    print("[Client] Server closed the connection.")
                    break

                response_str = response.decode("ascii")
                full_response += response_str

                if self.is_end_of_message(full_response):
                    break
            return full_response
        except socket.timeout:
            print("[Client] Read operation timed out.")
        except Exception as e:
            print(f"[Client] Error while receiving data: {e}")
        return None

    def is_end_of_message(self, response: str) -> bool:
        """Check if the end-of-message marker is reached."""
        return response.endswith("[EOM]") or "MESSAGEOK" in response

    def close(self):
        """Close the TCP connection."""
        if self.client_socket:
            self.client_socket.close()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\nGracefully stopping the client... Goodbye!")
    sys.exit(0)

def send_request(client: TCPClient, message: str):
    """Send the message and return the server's response."""
    response = client.send_data(message)
    if response is None:
        print("[Client] No response from server.")
    else:
        print(f"[Client] Full response received: {response}")
    return response

def initialize_client(connect_timeout=5, read_timeout=5) -> TCPClient:
    """Initialize the TCP client with connection and read timeouts."""
    client = TCPClient()
    client.connect(connect_timeout=connect_timeout, read_timeout=read_timeout)
    return client
