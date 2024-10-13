from scapy.all import IP, TCP, send, sniff, RandShort, RandInt
from queue import Queue
import base64
import signal

class TCPHandler:
    def __init__(
        self, iface: str = "en0", server_ip: str = "127.0.0.1", server_port: int = 12345
    ):
        self.iface = iface
        self.server_ip = server_ip
        self.server_port = server_port
        self.message_queue = Queue()  # Initialize a message queue

    def enqueue_message(self, message: str):
        self.message_queue.put(message)  # Add message to the queue

    def send_syn(self, max_retries: int = 5, timeout: int = 5):
        src_port = RandShort()
        seq_num = RandInt()

        # Define a filter for SYN-ACK
        filter_str = (
            f"tcp and src host {self.server_ip} and src port {self.server_port} "
            f"and dst port {src_port} and tcp[13] & 0x12 == 0x12"
        )

        for attempt in range(1, max_retries + 1):
            # Build SYN packet
            syn_packet = IP(dst=self.server_ip) / TCP(
                sport=src_port, dport=self.server_port, flags="S", seq=seq_num
            )

            print(
                f"[Client] Sending SYN to {self.server_ip}:{self.server_port} (Attempt {attempt})"
            )
            # Send SYN
            send(syn_packet, verbose=0, iface=self.iface)

            # Sniff for SYN-ACK
            synack = sniff(
                filter=filter_str, count=1, timeout=timeout, iface=self.iface
            )

            if synack:
                packet = synack[0]
                print(
                    f"[Client] Received SYN-ACK from {self.server_ip}:{self.server_port}"
                )

                # Calculate ACK numbers
                ack_num = packet[TCP].seq + 1
                ack_seq = packet[TCP].ack

                # Build ACK packet
                ack_packet = IP(dst=self.server_ip) / TCP(
                    sport=src_port,
                    dport=self.server_port,
                    flags="A",
                    seq=ack_seq,
                    ack=ack_num,
                )
                send(ack_packet, verbose=0, iface=self.iface)
                print(f"[Client] Sent ACK to {self.server_ip}:{self.server_port}")
                print("[Client] TCP three-way handshake completed")
                return True
            else:
                print("[Client] Did not receive SYN-ACK, retrying...")

        print("[Client] Handshake failed after maximum retries")
        return False

    def receive_and_process_message(self):
        """Receive and process TCP data for BOARDINFO and other fields."""
        print("[Client] Listening for TCP data...")

        # Simulate receiving data
        simulated_data = (
            "POSTBOARDCONTENT[NP]BOARDINFO[EQ]ew0KICAiaWQiOiA0MSwNCiAgInN0YXR1cyI6IDAsDQogICJ0YWJsZUxvY2F0aW9uIjogbnVsbCwNCiAgImNvbnRlbnQiOiBbDQogICAgew0KICAgICAgIml0ZW1JZCI6ICIzMDUiLA0KICAgICAgIml0ZW1UeXBlIjogMCwNCiAgICAgICJwYXJlbnRQb3NpdGlvbiI6IC0xLA0KICAgICAgInF1YW50aXR5IjogMS4wMDAwMDAsDQogICAgICAicHJpY2UiOiAyOC4wMDAwMDAsDQogICAgICAiYWRkaXRpb25hbEluZm8iOiBudWxsLA0KICAgICAgImd1aWQiOiAiY2NjMjUxMTgtNTExZC00OWE0LWIzZmUtNjcwZjA2M2VlZDU0IiwNCiAgICAgICJlbXBsb3llZSI6IDUsDQogICAgICAidGltZSI6IDE3Mjc5ODEwMTYwMDAsDQogICAgICAibGluZUxldmVsIjogMCwNCiAgICAgICJyYXRpbyI6IDAsDQogICAgICAidG90YWwiOiAyOC4wMDAwMDAsDQogICAgICAibGluZURpc2NvdW50IjogMC4wLA0KICAgICAgImNvbXBsZXRlZCI6IGZhbHNlLA0KICAgICAgInBhcmVudEd1aWQiOiAiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIg0KICAgIH0sDQogICAgew0KICAgICAgIml0ZW1JZCI6ICI5MDEiLA0KICAgICAgIml0ZW1UeXBlIjogMywNCiAgICAgICJwYXJlbnRQb3NpdGlvbiI6IDAsDQogICAgICAicXVhbnRpdHkiOiAxLjAwMDAwMCwNCiAgICAgICJwcmljZSI6IDAuMDAwMDAwLA0KICAgICAgImFkZGl0aW9uYWxJbmZvIjogbnVsbCwNCiAgICAgICJndWlkIjogImFkZjk4YzUwLWQ2ZTEtNGJiNi1hZDBmLTM0MjQ1OGEyZjdmMSIsDQogICAgICAiZW1wbG95ZWUiOiA1LA0KICAgICAgInRpbWUiOiAxNzI3OTgxMDE2MDAwLA0KICAgICAgImxpbmVMZXZlbCI6IDAsDQogICAgICAicmF0aW8iOiAxLA0KICAgICAgInRvdGFsIjogMC4wMDAwMDAsDQogICAgICAibGluZURpc2NvdW50IjogMC4wLA0KICAgICAgImNvbXBsZXRlZCI6IGZhbHNlLA0KICAgICAgInBhcmVudEd1aWQiOiAiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIg0KICAgIH0NCiAgXSwNCiAgInRvdGFsIjogMzEuMDgsDQogICJnbG9iYWxEaXNjb3VudCI6IDAuMDAwMDAwDQp9[NP]MESSAGETYPE[EQ]XDPeople.Entities.PostBoardInfoMessage[NP]MESSAGEID[EQ]d47e5fc4-d1ff-4f01-9166-f69e24c53184[NP]TERMINALID[EQ]1[EOM]"
        )

        # Extract BOARDINFO
        board_info_encoded = self.extract_field(simulated_data, "BOARDINFO")
        board_info_decoded = self.decode_base64(board_info_encoded)

        print(f"Decoded BOARDINFO: {board_info_decoded}")

        # Check if TERMINALID is present
        terminal_id = self.extract_field(simulated_data, "TERMINALID")
        if terminal_id == "1":
            print("Received TERMINALID = 1, EOM. TCP Session Closed.")

    def extract_field(self, data: str, field: str) -> str:
        """Extract the value of a field from the received data."""
        try:
            return data.split(f"[NP]{field}[EQ]")[1].split("[NP]")[0]
        except IndexError:
            return ""

    def decode_base64(self, base64_string: str) -> str:
        """Decode a Base64 encoded string."""
        try:
            return base64.b64decode(base64_string).decode("utf-8")
        except Exception as e:
            print(f"Error decoding Base64: {e}")
            return ""

