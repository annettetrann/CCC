from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    sql_get = f'UPDATE global_inventory\
         SET gold = 100,\
            num_red_potion = 0,\
            num_green_potion = 0,\
            num_blue_potion = 0,\
            num_red_ml = 0,\
            num_green_ml,\
            num_blue_ml\
    '
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "~ Magic Mushrooms ~",
        "shop_owner": "Annette Tran",
    }

