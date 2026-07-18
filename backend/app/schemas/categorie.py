from pydantic import BaseModel, ConfigDict


class CategorieCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    couleur: str
    nombre_liens: int
