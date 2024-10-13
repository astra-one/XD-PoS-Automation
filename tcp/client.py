import signal
from message_builder import MessageBuilder
from tcp_handler import TCPHandler

def test_message_builder():
    # Parameters for the test
    user_id = "0"
    protocol_version = "1"
    token = "88e90ba5d746ebf29e968500c10fcf74e155d799"
    board_id = "50"  # Example BOARDID

    # Create an instance of MessageBuilder
    message_builder = MessageBuilder(user_id, "1.0", protocol_version, token)

    # Build the message
    constructed_message = message_builder.build_get_board_content(board_id)

    # Print the constructed message
    print(constructed_message)

    # Add the constructed message to the TCPHandler's queue
    tcp_handler = TCPHandler()
    tcp_handler.enqueue_message(constructed_message)

    # Optionally print the message from the queue
    if not tcp_handler.message_queue.empty():
        print(f"Message in queue: {tcp_handler.message_queue.get()}")


def test_tcp_handler():
    server_ip = "127.0.0.1"
    server_port = 12345

    client = TCPHandler(server_ip=server_ip, server_port=server_port)
    success = client.send_syn()
    if success:
        print(f"Connection established with {server_ip}:{server_port}")
        client.receive_and_process_message()  # Simulate receiving and processing TCP message
    else:
        print(f"Failed to establish connection with {server_ip}:{server_port}")


def test_decoding_only():
    """Test only the decoding of the received message."""
    tcp_handler = TCPHandler()
    tcp_handler.receive_and_process_message()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\nGracefully stopping the program... Goodbye!")
    sys.exit(0)

def main():
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Run the test for decoding
    test_decoding_only()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
