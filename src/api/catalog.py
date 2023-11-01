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
    catalog = []

    potion_get = """SELECT SUM(potions_ledger.change) as quantity, potion_catalog.name, potion_catalog.price, potion_catalog.sku, potion_catalog.red, potion_catalog.green, potion_catalog.blue, potion_catalog.dark
                    FROM potions_ledger
                    JOIN potion_catalog ON potions_ledger.potion_id=potion_catalog.id
                    GROUP BY potion_id, potion_catalog.sku, potion_catalog.name, potion_catalog.price, potion_catalog.red, potion_catalog.green, potion_catalog.blue, potion_catalog.dark
                """
    with db.engine.begin() as connection:
        catalog_result = connection.execute(sqlalchemy.text(potion_get)).all()
        for potion in catalog_result:
            if potion.quantity > 0:
                catalog.append(
                    {
                        "sku": potion.sku,
                        "name": potion.name,
                        "quantity": potion.quantity,
                        "price": potion.price,
                        "potion_type": [potion.red, potion.green, potion.blue, potion.dark]
                    }
                )
    return catalog