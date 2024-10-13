from pydantic import BaseModel
from pydantic.fields import Field

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