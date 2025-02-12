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
    reset_global = f'UPDATE global_inventory\
         SET gold = 100,\
            num_red_ml = 0,\
            num_green_ml = 0,\
            num_blue_ml = 0,\
            num_dark_ml = 0'
    reset_potions = """UPDATE potion_catalog\
        SET quantity = 0"""
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(reset_global))
        connection.execute(sqlalchemy.text(reset_potions))

    #validate reset
    print("Successfully reset shop")

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """
    return {
        "shop_name": "~ Magic Mushrooms ~",
        "shop_owner": "Annette Tran",
    }

