from langchain_openai import ChatOpenAI
from prompt import order_process_prompt, comanda_template, validate_comanda_prompt, validate_template
import json
from models import ComandaData, ValidateData

class OrderProcessor:
    """
    This class processes and validates a 'comanda' in text format and returns the corrected orders.
    """

    def __init__(self, comanda: str, key: str):
        self.comanda = comanda
        self.model = ChatOpenAI(
            model_name="gpt-4o-mini-2024-07-18", temperature=0.0, openai_api_key=key
        )

    async def process_and_validate(self, detalhes: str = ""):
        """
        Process the 'comanda', validate it, and return the processed data along with validation status.
        """
        # Process the 'comanda'
        chain = order_process_prompt | self.model
        response = await chain.ainvoke(
            {
                "comanda": self.comanda,
                "json": comanda_template,
                "desconto": 2,
                "taxa_servico": 11,
                "detalhes": detalhes,
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

        # Validate the 'comanda'
        validation_response = await self.validate(comanda_data)

        return comanda_data, validation_response

    async def validate(self, comanda_data: ComandaData):
        """
        Validate the processed 'comanda'.
        """
        chain = validate_comanda_prompt | self.model
        response = await chain.ainvoke(
            {
                "comanda": self.comanda,
                "json": validate_template,
                "desconto": comanda_data.porcentagem_desconto,
                "taxa_servico": comanda_data.porcentagem_taxa_servico,
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
            validate_data = ValidateData.model_validate_json(formatted_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        return validate_data

    async def correct_comanda(self, comanda_data: ComandaData, detalhes: str):
        """
        Correct the 'comanda' based on validation feedback.
        """
        return await self.process_and_validate(detalhes)
