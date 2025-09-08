from models.entity_models import ComandaData
from langchain_openai import ChatOpenAI
from prompt import message_enhancer_prompt

class MessageBuilder:
    def __init__(self, order: ComandaData, key: str):
        self.order = order
        self.model = ChatOpenAI(
            model_name="gpt-4o-mini-2024-07-18", temperature=0.0, openai_api_key=key
        )

    def build_message(self):
        message_parts = []

        for pedido in self.order.pedidos:
            item_message = (
                f"🍽 {pedido.nome_prato}\n"
                f"{pedido.quantidade} pcs x € {pedido.preco_unitario:.2f} = € {pedido.quantidade * pedido.preco_unitario:.2f}"
            )
            message_parts.append(item_message)

        message_parts.append("\n-----------------------------------\n")

        summary_message = (
            f"✨ Service Fee: € {self.order.valor_taxa_servico:.2f}\n"
            f"💳 Gross Total: € {self.order.valor_total_bruto:.2f}\n"
            # f"💸 *Desconto* (*{self.order.porcentagem_desconto}*%): -R$ {(self.order.valor_desconto):.2f}\n"
            # "\n-----------------------------------\n"
            # f"*🔹 Total com Desconto: R$ {self.order.valor_total_desconto:.2f}*"
        )
        message_parts.append(summary_message)

        final_message = "\n\n".join(message_parts)
        return final_message
    
    async def message_enhancer(self):
        message = self.build_message()

        chain = message_enhancer_prompt | self.model

        response = await chain.ainvoke({"message": message})

        return response.content

    
    async def save_txt(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(await self.message_enhancer())
