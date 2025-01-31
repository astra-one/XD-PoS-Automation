import asyncio
import configparser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Dict
from prompt import (
    message_enhancer_prompt,
)  # Se ainda quiser usar o LLM para "refinar" a mensagem


# Modelo de cada pedido (internamente usaremos "nome_prato" e "preco_unitario")
class Pedido(BaseModel):
    nome_prato: str
    quantidade: int
    preco_unitario: float


# Modelo da comanda com valores calculados
class ComandaData(BaseModel):
    numero_comanda: int
    porcentagem_desconto: float = 2.0
    porcentagem_taxa_servico: float = 11.0
    valor_pratos: float = Field(default=0.0)
    valor_total_bruto: float = Field(default=0.0)
    valor_taxa_servico: float = Field(default=0.0)
    valor_desconto: float = Field(default=0.0)
    valor_total_desconto: float = Field(default=0.0)
    pedidos: List[Pedido]


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
        """
        Carrega a configuração (API Key da OpenAI, por exemplo) de um arquivo .ini
        """
        config = configparser.ConfigParser()
        config.read(config_path)
        self.api_key = config["Settings"]["openaiAPIKey"]

    def get_model(self):
        """Retorna um modelo ChatOpenAI para processamento (caso queira refinar mensagens)."""
        return ChatOpenAI(
            model_name="gpt-4o-mini-2024-07-18",
            temperature=0.0,
            openai_api_key=self.api_key,
        )

    def consolidate_comanda(self):
        """
        Consolida pedidos que tenham mesmo nome e mesmo preço unitário,
        somando as quantidades em um único item.
        """
        consolidated = {}
        for pedido in self.comanda_data.pedidos:
            # Ignore se preço unitário for zero (pode ser erro ou item não contabilizado)
            if pedido.preco_unitario == 0:
                continue

            key = (pedido.nome_prato, pedido.preco_unitario)
            if key in consolidated:
                consolidated[key].quantidade += pedido.quantidade
            else:
                consolidated[key] = pedido

        self.comanda_data.pedidos = list(consolidated.values())

    def build_message(self):
        """
        Monta a mensagem de saída listando os itens da comanda e os valores
        de taxa, total bruto e desconto.
        """
        message_parts = []

        for pedido in self.comanda_data.pedidos:
            subtotal = pedido.quantidade * pedido.preco_unitario
            item_message = (
                f"🍽 {pedido.nome_prato}\n"
                f"{pedido.quantidade} un. x R$ {pedido.preco_unitario:.2f} = R$ {subtotal:.2f}"
            )
            message_parts.append(item_message)

        message_parts.append("\n-----------------------------------\n")

        summary_message = (
            f"✨ Taxa de Serviço: R$ {self.comanda_data.valor_taxa_servico:.2f}\n"
            f"💳 Total Bruto: R$ {self.comanda_data.valor_total_bruto:.2f}\n"
            f"💸 Desconto: R$ {self.comanda_data.valor_desconto:.2f}\n"
            f"🏷 Total com Desconto: R$ {self.comanda_data.valor_total_desconto:.2f}"
        )
        message_parts.append(summary_message)

        # Junta tudo em uma única string
        final_message = "\n\n".join(message_parts)
        return final_message

    async def build_and_save_message(self, output_file: str = "") -> str:
        """
        Constrói a mensagem, opcionalmente envia para o modelo (para "refinar" o texto),
        e salva em arquivo, se desejado.
        """
        # 1. Cria a mensagem baseada na comanda
        message = self.build_message()

        # 2. Usa LLM para refinar a mensagem (opcional)
        chain = message_enhancer_prompt | self.get_model()
        response = await chain.ainvoke({"message": message})
        enhanced_message = response.content

        # 3. Salva em arquivo (se output_file for passado)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(enhanced_message)

        return enhanced_message

    async def main(
        self, items_list: List[Dict], numero_comanda: int = 1, output_file: str = ""
    ) -> dict:
        """
        Recebe a lista de itens (já no formato final) e constrói a comanda,
        com consolidação de pedidos, cálculo de valores e geração da mensagem.
        """

        # Carrega configuração (caso seja necessário)
        self.initialize_config("config.ini")

        # Constrói lista de pedidos no formato do nosso modelo 'Pedido'
        pedidos = []
        for item in items_list:
            pedidos.append(
                Pedido(
                    nome_prato=item.get("product_name", "Indefinido"),
                    quantidade=int(item.get("quantity", 1)),
                    preco_unitario=float(item.get("price", 0.0)),
                )
            )

        # Cria objeto ComandaData (valores default de desconto e taxa já definidos)
        self.comanda_data = ComandaData(numero_comanda=numero_comanda, pedidos=pedidos)

        # Calcula o valor dos pratos
        self.comanda_data.valor_pratos = sum(
            p.quantidade * p.preco_unitario for p in self.comanda_data.pedidos
        )
        # Calcula taxa de serviço
        self.comanda_data.valor_taxa_servico = (
            self.comanda_data.valor_pratos
            * self.comanda_data.porcentagem_taxa_servico
            / 100
        )
        # Total bruto
        self.comanda_data.valor_total_bruto = (
            self.comanda_data.valor_pratos + self.comanda_data.valor_taxa_servico
        )
        # Desconto
        self.comanda_data.valor_desconto = (
            self.comanda_data.valor_total_bruto
            * self.comanda_data.porcentagem_desconto
            / 100
        )

        # Consolida pedidos repetidos
        self.consolidate_comanda()

        # Calcula total com desconto
        self.comanda_data.valor_total_desconto = (
            self.comanda_data.valor_total_bruto - self.comanda_data.valor_desconto
        )

        # Exibe no console (opcional)
        print("-" * 25)
        print(f"Comanda #{self.comanda_data.numero_comanda} processada com sucesso!")
        for pedido in self.comanda_data.pedidos:
            subtotal = pedido.quantidade * pedido.preco_unitario
            print(f"{pedido.quantidade}x {pedido.nome_prato} - R$ {subtotal:.2f}")
        print(f"Taxa de serviço: R$ {self.comanda_data.valor_taxa_servico:.2f}")
        print(f"Total Bruto: R$ {self.comanda_data.valor_total_bruto:.2f}")

        # Constrói a mensagem final e (opcionalmente) salva em arquivo
        processed_message = await self.build_and_save_message(output_file)

        # Retorno final
        return {
            "status": "Message processed successfully",
            "message": processed_message,
            "details": {
                "total": self.comanda_data.valor_total_bruto,
                "orders": [p.dict() for p in self.comanda_data.pedidos],
            },
        }


if __name__ == "__main__":
    processor = OrderProcessorChain()

    # Exemplo de lista de itens já montada
    sample_items = [
        {
            "product_name": "Picanha na Chapa",
            "quantity": 2.0,
            "price": 43.5,
            "total": 87.0,
        },
        {
            "product_name": "Feijoada Completa",
            "quantity": 2.0,
            "price": 53.11,
            "total": 106.22,
        },
    ]

    # Executa passando a lista diretamente
    result = asyncio.run(
        processor.main(sample_items, numero_comanda=123, output_file="msg_output.txt")
    )
    print("\n\nResultado final:", result)
