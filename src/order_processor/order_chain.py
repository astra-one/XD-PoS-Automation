import asyncio
import configparser
import json
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from prompt import (
    order_process_prompt,
    comanda_template,
    pedido_template,
    message_enhancer_prompt,
)

class Pedido(BaseModel):
    nome_prato: str
    quantidade: int
    preco_unitario: float

class ComandaData(BaseModel):
    numero_comanda: int
    porcentagem_desconto: int = 2.0
    porcentagem_taxa_servico: int = 11.0
    valor_pratos: float = Field(default=0.0)
    valor_total_bruto: float = Field(default=0.0)
    valor_taxa_servico: float = Field(default=0.0)
    valor_desconto: float = Field(default=0.0)
    valor_total_desconto: float = Field(default=0.0)
    pedidos: list[Pedido]

class OrderProcessorChain:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(OrderProcessorChain, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.config = None
        self.api_key = None
        self.comanda_data = None

    def initialize_config(self, config_path: str):
        """Initializes configuration from the config file."""
        config = configparser.ConfigParser()
        config.read(config_path)
        self.api_key = config["Settings"]["openaiAPIKey"]

    def get_model(self):
        """Returns an instance of the ChatOpenAI model for processing."""
        return ChatOpenAI(
            model_name="gpt-4o-mini-2024-07-18",
            temperature=0.0,
            openai_api_key=self.api_key,
        )

    async def process_comanda(self, comanda_text: str):
        """Processes the 'comanda' and performs corrections if needed."""
        self.comanda_text = comanda_text
        chain = order_process_prompt | self.get_model()

        response = await chain.ainvoke(
            {
                "comanda_template": comanda_template,
                "pedido_template": pedido_template,
                "comanda": self.comanda_text,
            }
        )

        formatted_response = response.content

        # Clean up the response to get valid JSON
        if formatted_response.startswith("```json"):
            formatted_response = formatted_response[7:]
        if formatted_response.endswith("```"):
            formatted_response = formatted_response[:-3]

        formatted_response = formatted_response.strip()

        try:
            self.comanda_data = ComandaData.model_validate_json(formatted_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        self.comanda_data.valor_pratos = sum(
            pedido.quantidade * pedido.preco_unitario for pedido in self.comanda_data.pedidos
        )
        self.comanda_data.valor_taxa_servico = (
            self.comanda_data.valor_pratos * self.comanda_data.porcentagem_taxa_servico / 100
        )
        self.comanda_data.valor_total_bruto = (
            self.comanda_data.valor_pratos + self.comanda_data.valor_taxa_servico
        )
        self.comanda_data.valor_desconto = (
            self.comanda_data.valor_total_bruto * self.comanda_data.porcentagem_desconto / 100
        )

        # Step 1: Consolidate orders
        self.consolidate_comanda()

    def consolidate_comanda(self):
        """Step 1: Consolidates duplicate orders in the 'comanda'."""
        consolidated = {}
        for pedido in self.comanda_data.pedidos:
            if pedido.preco_unitario == 0:
                continue

            key = (pedido.nome_prato, pedido.preco_unitario)
            if key in consolidated:
                consolidated[key].quantidade += pedido.quantidade
            else:
                consolidated[key] = pedido
        self.comanda_data.pedidos = list(consolidated.values())

    def build_message(self):
        """Step 2: Builds the message to be saved."""
        message_parts = []

        for pedido in self.comanda_data.pedidos:
            item_message = (
                f"🍽 {pedido.nome_prato}\n"
                f"{pedido.quantidade} un. x R$ {pedido.preco_unitario:.2f} = R$ {pedido.quantidade * pedido.preco_unitario:.2f}"
            )
            message_parts.append(item_message)

        message_parts.append("\n-----------------------------------\n")

        summary_message = (
            f"✨ Taxa de Serviço: R$ {self.comanda_data.valor_taxa_servico:.2f}\n"
            f"💳 Total Bruto: R$ {self.comanda_data.valor_total_bruto:.2f}\n"
        )
        message_parts.append(summary_message)

        final_message = "\n\n".join(message_parts)
        return final_message

    async def build_and_save_message(self, output_file: str):
        """Step 3: Builds and saves the enhanced message to a text file."""
        message = self.build_message()

        # Enhancing message with the model
        chain = message_enhancer_prompt | self.get_model()

        response = await chain.ainvoke({"message": message})

        enhanced_message = response.content

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(enhanced_message)
    
        return enhanced_message

    async def main(self, comanda_text: str, output_file: str) -> str:
        """Main function to execute the chain of tasks with a given comanda string."""
        # Initialize configuration (path to the config file can be passed here)
        self.initialize_config("config.ini")

        # Step 1: Process and consolidate the comanda data
        await self.process_comanda(comanda_text)

        # Print result
        print("-" * 25)
        print("Comanda processed successfully!")
        for pedido in self.comanda_data.pedidos:
            print(
                f"{pedido.quantidade}x {pedido.nome_prato} - R$ {(pedido.quantidade * pedido.preco_unitario):.2f}"
            )
        print(f"Taxa de serviço: R$ {self.comanda_data.valor_taxa_servico:.2f}")
        print(f"Total Bruto: R$ {self.comanda_data.valor_total_bruto:.2f}")
        print(f"Desconto: R$ {self.comanda_data.valor_desconto:.2f}")
        print(f"Total com desconto: R$ {self.comanda_data.valor_total_desconto:.2f}")

        # Step 3: Build and save the message to a file
        processed_message =  await self.build_and_save_message(output_file)
        return {
            "status": "Message processed successfully",
            "message": processed_message,
            "details": {
                "total": self.comanda_data.valor_total_bruto,
            }
        }


if __name__ == "__main__":
    processor = OrderProcessorChain()

    # Example usage with a provided comanda string and output filename
    comanda_text_example = ""
    output_file_example = "msg_output.txt"

    asyncio.run(processor.main(comanda_text_example, output_file_example))
