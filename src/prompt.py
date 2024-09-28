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
{json}
Os itens estarão no formato NOME_ITEM QUANTIDADE PRECO_TOTAL_ITEM, para descobrir o preço unitário, divida o PRECO_TOTAL_PRATO pela QUANTIDADE.
Em caso de itens repetidos, some as quantidades e calcule o preço total.
O valor_total é o valor total da comanda, sem descontos.
O valor_taxa_servico deve ser calculado: {taxa_servico}% do valor_total.
O valor_final é o valor total com o desconto aplicado: {desconto}%
{detalhes}

{comanda}
"""

validate_template = {
    "is_valid": "Bool",
    "descricao": "String",
}

validate_comanda_prompt = """
Responda somente em JSON.
Preencha o seguinte JSON exemplo:
{json}
com as informações extraídas da comanda, e o campo 'is_valid' como 'true' caso a comanda seja válida, e 'false' caso contrário.
O valor_desconto deverá ser o valor total com o seguinte desconto aplicaco: {desconto}%
O valor_total já inclui a taxa de serviço de {taxa_servico}%
Caso a comanda seja inválida, preencha o campo 'descricao' com o motivo, em formato de prompt para outro modelo solucionar.

{comanda}
"""

message_enhancer_prompt = """
Altere os emojis de cada prato, adicionando emojis personalizados para cada prato.
Me retorne apenas o texto da mensagem com os emojis alterados.

{message}
"""

order_process_prompt = PromptTemplate.from_template(order_process_prompt)
validate_comanda_prompt = PromptTemplate.from_template(validate_comanda_prompt)
message_enhancer_prompt = PromptTemplate.from_template(message_enhancer_prompt)