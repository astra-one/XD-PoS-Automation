import socket
import signal
import sys
import time


class TCPClient:
    _instance = None  # Class-level attribute to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TCPClient, cls).__new__(cls)
        return cls._instance

    def __init__(
        self, source_ip="127.0.0.1", target_ip="192.168.15.100", target_port=8978
    ):
        # Initialize only once
        if not hasattr(self, '_initialized'):
            self.source_ip = source_ip
            self.target_ip = target_ip
            self.target_port = target_port
            self.client_socket = None
            self.read_timeout = None  # Initialize read_timeout attribute
            self._initialized = True  # Flag to prevent re-initialization

    def connect(self, connect_timeout=None, read_timeout=None):
        """Establish the TCP connection."""
        try:
            self.client_socket = self.create_socket()
            if connect_timeout is not None:
                self.client_socket.settimeout(connect_timeout)
            self.client_socket.connect((self.target_ip, self.target_port))
            self.read_timeout = read_timeout  # Store read_timeout for use in receive_response
            if read_timeout is not None:
                self.client_socket.settimeout(read_timeout)
            #print("[Client] Connected to the server.")
        except Exception as e:
            #print(f"[Client] Connection error: {e}")
            self.client_socket = None

    def create_socket(self):
        """Create a TCP socket."""
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_data(self, message):
        """Send ASCII-encoded message to the server."""
        if self.client_socket is None:
            #print("[Client] Not connected to the server.")
            return None

        try:
            self.client_socket.sendall(message.encode("ascii"))
            #print(f"[Client] Sent message: {message}")
            return self.receive_response()
        except Exception as e:
            #print(f"[Client] Error during send or receive: {e}")
            self.close()  # Close the connection on error
            return None

    def receive_response(self):
        """Receive data from the server and return the full response."""
        full_response = ""
        start_time = time.time()  # Record the start time
        timeout_duration = self.read_timeout if self.read_timeout else 5  # Default to 5 seconds if not set
        try:
            while True:
                # Check if timeout has been exceeded
                if time.time() - start_time > timeout_duration:
                    #print("[Client] Receive operation timed out.")
                    self.close()
                    return None

                response = self.client_socket.recv(1024)
                if not response:
                    #print("[Client] Server closed the connection.")
                    self.close()
                    break

                response_str = response.decode("ascii")
                full_response += response_str
                #print(f"[Client] Received chunk: {response_str}")

                if self.is_end_of_message(full_response):
                    break
            return full_response
        except socket.timeout:
            #print("[Client] Read operation timed out.")
            self.close()
            return None
        except Exception as e:
            #print(f"[Client] Error while receiving data: {e}")
            self.close()
            return None

    def is_end_of_message(self, response: str) -> bool:
        """Check if the end-of-message marker is reached."""
        return response.endswith("[EOM]") or "MESSAGEOK" in response

    def close(self):
        """Close the TCP connection."""
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            #print("[Client] Connection closed.")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    #print("\nGracefully stopping the client... Goodbye!")
    sys.exit(0)


def send_request(client: TCPClient, message: str):
    """Send the message and return the server's response."""
    response = client.send_data(message)
    if response is None:
        pass
        #print("[Client] No response from server.")
    else:
        pass
        #print(f"[Client] Full response received: {response}")
    return response


def initialize_client(connect_timeout=5, read_timeout=5) -> TCPClient:
    """Initialize the TCP client with connection and read timeouts."""
    client = TCPClient()
    client.connect(connect_timeout=connect_timeout, read_timeout=read_timeout)
    return client


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    client = initialize_client(connect_timeout=5, read_timeout=5)

    messages = ["Hello, Server!", "How are you?", "Goodbye!"]
    for msg in messages:
        response = send_request(client, msg)
        if response is None:
            break  # Stop if there's no response or an error occurs

    # Close the connection when done
    client.close()
