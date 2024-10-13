import argparse
import asyncio
import configparser
from processor import OrderProcessor
from message_builder import MessageBuilder
from models import ComandaData


def read_config_file(filename: str) -> configparser.ConfigParser:
    """Reads and returns the configuration file."""
    config = configparser.ConfigParser()
    config.read(filename)
    return config


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Process a 'comanda'")
    parser.add_argument(
        "comanda_file", type=str, help="File containing the 'comanda' to be processed"
    )
    return parser.parse_args()


def read_comanda_file(filename: str) -> str:
    """Reads the content of the 'comanda' file."""
    if not filename:
        raise ValueError("The 'comanda' file name cannot be empty")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise ValueError(f"File {filename} not found")


async def process_comanda(comanda_text: str, api_key: str):
    """Processes the 'comanda' and performs corrections if needed."""
    processor = OrderProcessor(comanda_text, api_key)
    comanda_data = await processor.process_data()
    consolidate_comanda(comanda_data)

    return comanda_data


def consolidate_comanda(comanda_data: ComandaData):
    consolidated = {}
    for pedido in comanda_data.pedidos:
        key = (pedido.nome_prato, pedido.preco_unitario)
        if key in consolidated:
            consolidated[key].quantidade += pedido.quantidade
        else:
            consolidated[key] = pedido
    comanda_data.pedidos = list(consolidated.values())


async def build_and_save_message(comanda_data, api_key: str, output_file: str):
    """Builds and saves the message to a text file."""
    message_builder = MessageBuilder(comanda_data, api_key)
    await message_builder.save_txt(output_file)


import os


async def main():
    """Main function to execute the script logic."""
    args = parse_arguments()
    comanda_text = read_comanda_file(args.comanda_file)

    config = read_config_file("config.ini")["Settings"]
    api_key = config["openaiAPIKey"]

    comanda_data = await process_comanda(comanda_text, api_key)

    print("-" * 25)
    print("Comanda processed successfully!")
    for pedido in comanda_data.pedidos:
        print(
        f"{pedido.quantidade}x {pedido.nome_prato} - R$ {(pedido.quantidade * pedido.preco_unitario):.2f}"
        )
    print(f"Taxa de serviço: R$ {comanda_data.valor_taxa_servico:.2f}")
    print(f"Total Bruto: R$ {comanda_data.valor_total_bruto:.2f}")
    print(f"Desconto: R$ {comanda_data.valor_desconto:.2f}")
    print(f"Total com desconto: R$ {comanda_data.valor_total_desconto:.2f}")

    # Extract comanda number from the filename
    comanda_number = os.path.splitext(os.path.basename(args.comanda_file))[0].split(
        "_"
    )[-1]
    message_filename = f"msg_{comanda_number}.txt"

    await build_and_save_message(comanda_data, api_key, message_filename)


if __name__ == "__main__":
    asyncio.run(main())
