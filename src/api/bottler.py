from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(f"BOTTLE DELIVERY: \n {potions_delivered}")
    
    red_ml_used = 0
    green_ml_used = 0
    blue_ml_used = 0
    dark_ml_used = 0

    with db.engine.begin() as connection:
        for potion in potions_delivered:
            r = potion.potion_type[0]
            g = potion.potion_type[1]
            b = potion.potion_type[2]
            d = potion.potion_type[3]

            #add barrel ml
            red_ml_used += (r*potion.quantity)
            green_ml_used += (g*potion.quantity)
            blue_ml_used += (b*potion.quantity)
            dark_ml_used += (d*potion.quantity)

            sql_potions = """UPDATE potion_catalog
                            SET quantity = quantity + :quant
                            WHERE red = :r, green = :g, blue = :b, dark = :d"""
            connection.execute(sqlalchemy.text(sql_potions), 
                    [{"quant": potion.quantity, "r": r, "g": g, "b": b, "d": d}])
            print(f"Bottle Delivery: {potion.quantity} {potion.potion_type}")
        #update ml used in globals inventory
        sql_global = """UPDATE global_inventory
                        SET num_red_ml = num_red_ml - :red_ml_used,
                        num_green_ml = num_green_ml - :green_ml_used,
                        num_blue_ml = num_blue_ml - :blue_ml_used,
                        num_dark_ml = num_dark_ml - :dark_ml_used"""
        connection.execute(sqlalchemy.text(sql_global), 
            [{"red_ml_used": red_ml_used, "green_ml_used": green_ml_used, "blue_ml_used": blue_ml_used, "dark_ml_used": dark_ml_used}])
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    print("BOTTLE PLAN: ")

    # Logic: bottle up the most of the potions we have the least.
    request_potions = []
    with db.engine.begin() as connection:
        globals_result = connection.execute(sqlalchemy.text("SELECT *\
                                                    FROM global_inventory")).one()
        
        print(f"globals inventory: {globals_result}")
        inventory_red_ml = globals_result.num_red_ml
        inventory_green_ml = globals_result.num_green_ml
        inventory_blue_ml = globals_result.num_blue_ml 
        inventory_dark_ml = globals_result.num_dark_ml

        catalog_result = connection.execute(sqlalchemy.text("SELECT sku, quantity, red, green, blue, dark\
                                                    FROM potion_catalog\
                                                    ORDER BY quantity ASC")).all()
        print(f"catalog result: {catalog_result}")

        for potion in catalog_result:
            if (potion.red > inventory_red_ml) or (potion.green > inventory_green_ml) or (potion.blue > inventory_blue_ml) or (potion.dark > inventory_dark_ml):
                print(f"Tried to make {potion.sku}, but there was not enough inventory to make at least 1")
                continue
            #there is enough to make just 1 
            max_create = []
            if (potion.red > 0):
                max_create.append(inventory_red_ml//potion.red)
            if(potion.green > 0):
                max_create.append(inventory_green_ml//potion.green)
            if(potion.blue > 0):
                max_create.append(inventory_blue_ml//potion.blue)
            if(potion.dark > 0):
                max_create.append(inventory_dark_ml//potion.dark)

            #the most we can create is the amount we can handle
            request_num = min(max_create)

            if request_num > 0:
                if potion.red > 0:
                    inventory_red_ml -= request_num*potion.red
                if potion.green > 0:
                    inventory_green_ml -= request_num*potion.green
                if potion.blue > 0:
                    inventory_blue_ml -= request_num*potion.blue
                if potion.dark > 0:
                    inventory_dark_ml -= request_num*potion.dark
                request_potions.append(
                    {
                        "potion_type": [potion.red, potion.green, potion.blue, potion.dark],
                        "quantity": request_num
                    }
                )
            print(f"-> requesting {request_num} {potion.sku}")

    return request_potions
