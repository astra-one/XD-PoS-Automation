import socket
import signal
import sys

class TCPClient:
    def __init__(self, source_ip="127.0.0.1", target_ip="127.0.0.1", target_port=8978):
        self.source_ip = source_ip
        self.target_ip = target_ip
        self.target_port = target_port
        self.client_socket = None

    def connect(self, connect_timeout=None, read_timeout=None):
        """Establish the TCP connection (SYN process)."""
        try:
            # Create a TCP socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if connect_timeout is not None:
                self.client_socket.settimeout(connect_timeout)
            print(f"[Client] Connecting to {self.target_ip}:{self.target_port}...")
            self.client_socket.connect((self.target_ip, self.target_port))
            print(f"[Client] Connection established with {self.target_ip}:{self.target_port}")
            # After connecting, set the read timeout
            if read_timeout is not None:
                self.client_socket.settimeout(read_timeout)
        except socket.timeout:
            print(f"[Client] Connection to {self.target_ip}:{self.target_port} timed out.")
            self.client_socket = None
        except ConnectionRefusedError:
            print(f"[Client] Connection refused by {self.target_ip}:{self.target_port}.")
            self.client_socket = None
        except Exception as e:
            print(f"[Client] An error occurred during connection: {e}")
            self.client_socket = None

    def send_data(self, message, connect_timeout=None, read_timeout=None):
        """Send ASCII-encoded message to the server."""
        if self.client_socket is None:
            print("[Client] Not connected to the server.")
            return

        try:
            # Send the message
            self.client_socket.sendall(message.encode("ascii"))
            print(f"[Client] Sent: {message}")

            # Listen for server responses until the end-of-message marker is received
            full_response = ""
            while True:
                response = self.client_socket.recv(1024)
                if not response:
                    print("[Client] Server closed the connection.")
                    break

                # Decode and append the received data
                response_str = response.decode("ascii")
                full_response += response_str
                print(f"[Client] Received: {response_str}")

                # Check for end-of-message markers
                if full_response.endswith("[EOM]") or "MESSAGEOK" in full_response:
                    print("[Client] End of message received.")
                    break

            return full_response

        except socket.timeout:
            print("[Client] Read operation timed out.")
        except Exception as e:
            print(f"[Client] An error occurred while sending data: {e}")
        finally:
            self.close()

    def close(self):
        """Close the TCP connection."""
        if self.client_socket:
            self.client_socket.close()
            print("[Client] Connection closed.")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\nGracefully stopping the client... Goodbye!")
    sys.exit(0)

def main():
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize the client and connect to the server
    client = TCPClient()
    # Set timeouts similar to Java code (e.g., 5 seconds for connect and read timeouts)
    connect_timeout = 5
    read_timeout = 5
    client.connect(connect_timeout=connect_timeout, read_timeout=read_timeout)

    # The custom message you want to send
    message = """GETBOARDCONTENT
[NP]PROTOCOLVERSION[EQ]1
[NP]BOARDID[EQ]50
[NP]TYPE[EQ]1
[NP]USERID[EQ]1
[NP]TOKEN[EQ]0f291e94973f249beca6bbf16fbeb53e6ea38aba
[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetBoardInfoMessage
[NP]MESSAGEID[EQ]e777b2af-72c7-4e95-a1d2-548b8151dcfe[EOM]
"""

    # Send the message to the server
    response = client.send_data(message)
    print(f"[Client] Full response received: {response}")

if __name__ == "__main__":
    main()
