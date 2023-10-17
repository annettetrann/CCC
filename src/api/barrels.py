from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print("BARREL DELIVERY: ")
    #initalize all new values 
    added_red_ml = 0
    added_green_ml = 0
    added_blue_ml = 0
    added_dark_ml = 0
    gold_paid = 0

    for barrel in barrels_delivered:
        print(f'Barrels Delivered: {barrel}')
        print(f'Puchased {barrel.quantity} of {barrel.sku}({barrel.ml_per_barrel}ml)')

        gold_paid += barrel.quantity*barrel.price

        if (barrel.potion_type == [1, 0, 0, 0]): #red
            added_red_ml += barrel.quantity*barrel.ml_per_barrel
            print(f'Adding {added_red_ml}ml of red')
        elif (barrel.potion_type == [0, 1, 0, 0]): #green
            added_green_ml += barrel.quantity*barrel.ml_per_barrel
            print(f'Adding {added_green_ml}ml of green')
        elif (barrel.potion_type == [0, 0, 1, 0]): #blue
            added_blue_ml += barrel.quantity*barrel.ml_per_barrel
            print(f'Adding {added_blue_ml}ml of blue')
        elif(barrel.potion_type == [0, 0, 0, 1]): #dark
            added_dark_ml += barrel.quantity*barrel.ml_per_barrel
            print(f'Adding {added_dark_ml}ml of dark')
        else:
            raise Exception("Invalid Potion Type")
    
    #print the total of newly added liquids 
    print(f"Barrel Delivery Summary:\
          Added Red ml : {added_red_ml},\
          Added Green ml : {added_green_ml},\
          Added Blue ml : {added_blue_ml},\
          Added Dark ml : {added_dark_ml},\
          Gold Paid : {gold_paid}")
    
    #update database
    with db.engine.begin() as connection:
        update_sql = """UPDATE global_inventory
                        SET num_red_ml = num_red_ml + :added_red_ml,
                        num_green_ml = num_green_ml + :added_green_ml,
                        num_blue_ml = num_blue_ml + :added_blue_ml,
                        num_dark_ml = num_dark_ml + :added_dark_ml,
                        gold = gold - :gold_paid"""
    
        connection.execute(sqlalchemy.text(update_sql), 
            [{"added_red_ml": added_red_ml, "added_green_ml": added_green_ml, "added_blue_ml": added_blue_ml, "added_dark_ml": added_dark_ml, "gold_paid": gold_paid}])


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("BARREL PLAN: ")

    print(f'Wholesale catalog: {wholesale_catalog}')

    sorted_catalog = sort_barrels(wholesale_catalog)
    #print(f"Sorted Catalog: {sorted_catalog}")

    request_barrels = []
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT *
                                                    FROM global_inventory""")).one()
    print(f"Inventory Gold: {result.gold}")

    inventory_gold = result.gold

    #create a tuple of (potion_type, color_ml)
    red_inventory = ("red", [100, 0 , 0, 0], result.num_red_potion)
    green_inventory = ("green", [0, 100 , 0, 0], result.num_green_potion)
    blue_inventory = ("blue", [0, 0 , 100, 0], result.num_blue_potion)
    dark_inventory = ("dark", [0, 0 , 0, 100], result.num_dark_potion) #add in dark potion
    priority = [red_inventory, green_inventory, blue_inventory, dark_inventory]

    #create a priority list based on which potions are least stocked
    #CHANGE TO: least stocked ml
    priority.sort(key=sort_third)
    print(f"Sorted Priority: {priority}")

    #start buying barrels
    for i in range(len(priority)):
        potion_color_str = priority[i][0]
        potion_inventory = priority[i][2]
        print(f"Current Priority: {potion_color_str} ({i}), Inventory = {potion_inventory} potions")
        
        #make sure those potions exist & availale to purchase
        if potion_color_str not in sorted_catalog:
            print(f"Wanted to buy some {potion_color_str} barrels, but there are none for sale at this time :(")
            continue #just move onto the next potion type

        select_catalog = sorted_catalog[potion_color_str]
        #print(f'Select Catalog: {select_catalog}')

        current_request, inventory_gold = balance_requests(select_catalog, inventory_gold)
        request_barrels.extend(current_request)
        print(f"Requesting {request_barrels}")
        print(f"Inventory Gold: {inventory_gold}")

    print(f'Requesting Barrels: \n{request_barrels}')
    
    return request_barrels

#current purchasing logic: maximize purchase of top priority
def balance_requests(select_catalog, inventory_gold):
    request = []
    request_quantity = 0
    for barrel in select_catalog:
        #usually first items are largest available to smallest
        request_quantity = inventory_gold//barrel.price
        if request_quantity > barrel.quantity: #if request is more than wholesale quant
            request_quantity = barrel.quantity # request max
        if request_quantity > 0: # add the request if exists
            request.append(
                {"sku": barrel.sku,
                 "quantity": request_quantity}
                 )
            inventory_gold -= (request_quantity*barrel.price)
    
    return request, inventory_gold
        

def sort_third(ls):
    return ls[2]

def sort_barrels(wholesale_catalog: list[Barrel]):
    sorted_catalog = {}
    for barrel in wholesale_catalog:
        if (barrel.potion_type == [1, 0, 0, 0]):
            if ("red" not in sorted_catalog):
                sorted_catalog["red"] = [barrel]
            else:
                sorted_catalog["red"].append(barrel)

        elif (barrel.potion_type == [0, 1, 0, 0]):
            if ("green" not in sorted_catalog):
                sorted_catalog["green"] = [barrel]
            else:
                sorted_catalog["green"].append(barrel)
        elif (barrel.potion_type == [0, 0, 1, 0]):
            if ("blue" not in sorted_catalog):
                sorted_catalog["blue"] = [barrel]
            else:
                sorted_catalog["blue"].append(barrel)
        elif (barrel.potion_type == [0, 0, 0, 1]):
            if ("dark" not in sorted_catalog):
                sorted_catalog["dark"] = [barrel]
            else:
                sorted_catalog["dark"].append(barrel)
        else:
            raise Exception("Undefined Potion Type")
    
    return sorted_catalog