from langchain.prompts import PromptTemplate

pedido_template = {
    "nome_prato": "String",
    "quantidade": "Int",
    "preco_unitario": "Float",
}

comanda_template = {
    "numero_comanda": "String",
    "pedidos": [pedido_template],
}

order_process_prompt = """
Responda somente em JSON.
Preencha o seguinte JSON exemplo:
{comanda_template}

Separe os itens seguindo o template: {pedido_template}
O pedido estará no formato NOME_ITEM'x' QUANTIDADE PRECO_UNITARIO = PRECO_TOTAL_ITEM
Caso não haja PRECO_UNITARIO, divida o PRECO_TOTAL_ITEM pela QUANTIDADE.

{comanda}
"""

consolidate_template = """
Resposta somente em JSON.

A partir do JSON fornecido, junte todos os pedidos que tiverem o mesmo nome e valor unitário.
Caso o valor unitário seja diferente, mantenha os pedidos separados.
Me retorne apenas o JSON com os pedidos consolidados.

{comanda_data}
"""

message_enhancer_prompt = """
Altere os emojis de cada prato, adicionando emojis personalizados para cada prato.
Me retorne apenas o texto da mensagem com os emojis alterados, e as casas decimais utilizando virgula.

{message}
"""

order_process_prompt = PromptTemplate.from_template(order_process_prompt)
message_enhancer_prompt = PromptTemplate.from_template(message_enhancer_prompt)
consolidate_prompt = PromptTemplate.from_template(consolidate_template)