from langchain.prompts import PromptTemplate

pedido_template = {
    "nome_prato": "String",
    "quantidade": "Int",
    "preco_unitario": "Float",
}

comanda_template = {
    "numero_comanda": "Int",
    "pedidos": [pedido_template],
}

order_process_prompt = """
Answer only in JSON.
Fill the following JSON example:
{comanda_template}

Separate items following the template: {pedido_template}
The order will be in the format ITEM_NAME 'x' QUANTITY UNIT_PRICE = ITEM_TOTAL
If there is no UNIT_PRICE, divide ITEM_TOTAL by QUANTITY.

{comanda}
"""

consolidate_template = """
Respond only in JSON.

From the provided JSON, merge all orders that have the same name and unit price.
If the unit price differs, keep the orders separate.
Return only the JSON with the consolidated orders.

{comanda_data}
"""

message_enhancer_prompt = """
Adjust the emojis for each dish, adding appropriate emojis per item.
Return only the message text with updated emojis, using the euro symbol (€) and comma decimal separators.

{message}
"""

order_process_prompt = PromptTemplate.from_template(order_process_prompt)
message_enhancer_prompt = PromptTemplate.from_template(message_enhancer_prompt)
consolidate_prompt = PromptTemplate.from_template(consolidate_template)