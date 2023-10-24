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

            #update potion count (+)
            
            #get potion id of matching potion based on rgb values 
            potion_info = (connection.execute(sqlalchemy.text("""SELECT id
                            FROM potion_catalog
                            WHERE red = :r and green = :g and blue = :b and dark = :d"""), 
                    [{"quant": potion.quantity, "r": r, "g": g, "b": b, "d": d}])).one()

            #update potions ledger 
            description = "bottle delivery"
            potions_ledger = """INSERT INTO potions_ledger (potion_id, change, description)
                            VALUES (:potion_id, :added_potions, :description)"""
            connection.execute(sqlalchemy.text(potions_ledger),
                             [{"potion_id": potion_info.id, "added_potions": potion.quantity, "description": description}])
            print(f"Bottle Delivery: {potion.quantity} {potion.potion_type}")

        #update mls in barrels (-)
        barrel_description = "bottled potions"
        barrel_ml_update = """INSERT INTO barrels_ledger (barrel_id, change, description)
                        VALUES 
                        (1, :red_ml_used, :barrel_description),
                        (2, :green_ml_used, :barrel_description),
                        (3, :blue_ml_used, :barrel_description),
                        (4, :dark_ml_used, :barrel_description)"""
        connection.execute(sqlalchemy.text(barrel_ml_update),
                             [{"red_ml_used": -red_ml_used,
                               "green_ml_used": -green_ml_used,
                               "blue_ml_used": -blue_ml_used,
                               "dark_ml_used": -dark_ml_used, 
                               "barrel_description": barrel_description}])
        
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
        #get the barrel and gold inventory 
        red_result = connection.execute(sqlalchemy.text("""SELECT sum(change) as total_ml
                                                            FROM barrels_ledger
                                                            WHERE barrel_id = 1""")).one()

        green_result = connection.execute(sqlalchemy.text("""SELECT sum(change) as total_ml
                                                            FROM barrels_ledger
                                                            WHERE barrel_id = 2""")).one()
    
        blue_result = connection.execute(sqlalchemy.text("""SELECT sum(change) as total_ml
                                                            FROM barrels_ledger
                                                            WHERE barrel_id = 3""")).one()
    
        dark_result = connection.execute(sqlalchemy.text("""SELECT sum(change) as total_ml
                                                            FROM barrels_ledger
                                                            WHERE barrel_id = 4""")).one()
        
        # print(f"globals inventory: {globals_result}")
        inventory_red_ml = red_result.total_ml
        print(f"Red ml Inventory = {inventory_red_ml}")
        inventory_green_ml = green_result.total_ml
        print(f"Green ml Inventory = {inventory_green_ml}")
        inventory_blue_ml = blue_result.total_ml
        print(f"Blue ml Inventory = {inventory_blue_ml}")
        inventory_dark_ml = dark_result.total_ml
        print(f"Dark ml Inventory = {inventory_dark_ml}")



        catalog_result = connection.execute(sqlalchemy.text("SELECT id\
                                                            FROM potion_catalog")).all()
        
        #get potion quant of all potion types and store in array
        potion_inventory = {}
        for potion in catalog_result:
            # SUM to get the quant of the current potion
            potion_quant_result = (connection.execute(sqlalchemy.text("""SELECT SUM(change) quantity
                                                                        FROM potions_ledger
                                                                        WHERE potion_id = :curr_potion_id"""), 
                                                                        [{"curr_potion_id": potion.id}])).one()
            
            potion_inventory[potion.id] = potion_quant_result.quantity
        
    #print(f"potion inventory: {potion_inventory}")
        #sort the quantity dictionary by ascending
        sorted_catalog = sorted(potion_inventory, key= potion_inventory.get)
        #only keys should be returned and in list form
        print(f"sorted catalog: {sorted_catalog}")

        for potion_id in sorted_catalog:
            potion = (connection.execute(sqlalchemy.text("SELECT id, sku, red, green, blue, dark\
                                                    FROM potion_catalog\
                                                    WHERE id = :potion_id"), 
                                                    [{"potion_id": potion_id}])).one()

            

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

            #the most we can create is the amount we can handle OR max = 75
            max_potions_inventory = 75 - potion.quantity
            max_create.append(max_potions_inventory)
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
