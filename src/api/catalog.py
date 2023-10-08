from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    #get updated catalog
    
    with db.engine.begin() as connection:
        #returns an array I am trying to update
        result = connection.execute(sqlalchemy.text("SELECT *\
                                                              FROM global_inventory")).one()
        return [
                {
                    "sku": "RED_POTION",
                    "name": "red potion",
                    "quantity": result.num_red_potion,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]
