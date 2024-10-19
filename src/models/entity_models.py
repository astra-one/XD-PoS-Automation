from typing import List, Optional
from pydantic import BaseModel, Field

class Table(BaseModel):
    id: int
    name: str
    status: int # 2 = Pagaram e resetou a comanda (Azul), 0 = Não aberta (Verde), 1 = Aberta (Vermelho) 
    lockDescription: Optional[str] = None
    inactive: bool
    freeTable: bool
    initialUser: int

class BoardItem(BaseModel):
    itemId: str
    itemType: int
    parentPosition: int
    quantity: float
    price: float
    additionalInfo: Optional[str] = None
    guid: str
    employee: int
    time: int
    lineLevel: int
    ratio: int
    total: float
    lineDiscount: float
    completed: bool
    parentGuid: str

class BoardResponseItem(BoardItem):
    itemName: Optional[str] = None  # Add itemName field

class BoardResponse(BaseModel):
    id: int
    status: int
    tableLocation: Optional[str]
    content: List[BoardResponseItem]
    total: float
    globalDiscount: float

class Product(BaseModel):
    id: Optional[int]
    name: Optional[str]
    parentId: Optional[int] = None  # Default to None if not provided
    visible: Optional[bool] = None  # Default to None if not provided

