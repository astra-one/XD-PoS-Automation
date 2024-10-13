from langchain_openai import ChatOpenAI
from prompt import order_process_prompt, comanda_template, pedido_template, consolidate_prompt
import json
from models import ComandaData

class OrderProcessor:
    """
    This class processes and validates a 'comanda' in text format and returns the corrected orders.
    """

    def __init__(self, comanda: str, key: str):
        self.comanda = comanda
        self.model = ChatOpenAI(
            model_name="gpt-4o-mini-2024-07-18", temperature=0.0, openai_api_key=key
        )

    async def process_data(self, detalhes: str = ""):
        chain = order_process_prompt | self.model
        response = await chain.ainvoke(
            {
                "comanda_template": comanda_template,
                "pedido_template": pedido_template,
                "comanda": self.comanda,
            }
        )

        formatted_response = response.content

        # Clean up the response to get valid JSON
        if formatted_response.startswith("```json"):
            formatted_response = formatted_response[7:]
        if formatted_response.endswith("```"):
            formatted_response = formatted_response[:-3]

        formatted_response = formatted_response.strip()

        # print(formatted_response)

        try:
            comanda_data = ComandaData.model_validate_json(formatted_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        comanda_data.valor_pratos = sum(
            pedido.quantidade * pedido.preco_unitario for pedido in comanda_data.pedidos
        )
        comanda_data.valor_taxa_servico = comanda_data.valor_pratos * comanda_data.porcentagem_taxa_servico / 100
        comanda_data.valor_total_bruto = comanda_data.valor_pratos + comanda_data.valor_taxa_servico
        comanda_data.valor_desconto = comanda_data.valor_total_bruto * comanda_data.porcentagem_desconto / 100
        comanda_data.valor_total_desconto = comanda_data.valor_total_bruto - comanda_data.valor_desconto

        return comanda_data