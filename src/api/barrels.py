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
    gold_paid = 0
    delivery_description = ''
    ml_added = 0

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            print(f'Barrels Delivered: {barrel}')
            print(f'Puchased {barrel.quantity} of {barrel.sku}({barrel.ml_per_barrel}ml)')
            
            gold_paid = (barrel.quantity*barrel.price)*-1
            ml_added = barrel.quantity*barrel.ml_per_barrel
            delivery_description = f'barrel delivery | {barrel.quantity} {barrel.sku} | {barrel.ml_per_barrel} ml'

            if (barrel.potion_type == [1, 0, 0, 0]): #red
                update_barrel = """INSERT INTO barrels_ledger (barrel_id, description, change)
                            VALUES (1, :delivery_description, :barrel_ml)"""
            elif (barrel.potion_type == [0, 1, 0, 0]): #green
                update_barrel = """INSERT INTO barrels_ledger (barrel_id, description, change)
                            VALUES (2, :delivery_description, :barrel_ml)"""
            elif (barrel.potion_type == [0, 0, 1, 0]): #blue
                update_barrel = """INSERT INTO barrels_ledger (barrel_id, description, change)
                            VALUES (3, :delivery_description, :barrel_ml)"""
            elif(barrel.potion_type == [0, 0, 0, 1]): #dark
                update_barrel = """INSERT INTO barrels_ledger (barrel_id, description, change)
                            VALUES (4, :delivery_description, :barrel_ml)"""
            else:
                raise Exception("Invalid Potion Type")
                continue

            #update barrel inventory
            connection.execute(sqlalchemy.text(update_barrel), 
                    [{"delivery_description": delivery_description, "barrel_ml": ml_added}])
            
            # update gold 
            connection.execute(sqlalchemy.text("""INSERT INTO gold_inventory (change, description)
                                                VALUES (:gold_paid, :description)"""),
                                                [{"gold_paid": gold_paid, "description": delivery_description}])
        
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
        #get the barrel inventory 
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
    #get the current gold inventory by summing up the balance
        gold_result = connection.execute(sqlalchemy.text("""SELECT sum(change) AS balance
                                                            FROM gold_inventory""")).one()
        
        print(f"Inventory Gold: {gold_result.balance}")

    inventory_gold = gold_result.balance
    #create a tuple of (potion_type, color_ml)
    red_inventory = ("red", [100, 0 , 0, 0], red_result.total_ml)
    green_inventory = ("green", [0, 100 , 0, 0], green_result.total_ml)
    blue_inventory = ("blue", [0, 0 , 100, 0], blue_result.total_ml)
    dark_inventory = ("dark", [0, 0 , 0, 100], dark_result.total_ml) #add in dark potion
    priority = [red_inventory, green_inventory, blue_inventory, dark_inventory]

    #create a priority list based on which potions are least stocked
    #CHANGE TO: least stocked ml
    priority.sort(key=sort_third)
    print(f"Sorted Priority: {priority}")

    #start buying barrels
    for i in range(len(priority)):
        potion_color_str = priority[i][0]
        potion_inventory = priority[i][2]
        print(f"Current Priority: {potion_color_str} ({i}), Inventory = {potion_inventory} ml")
        
        #make sure those potions exist & availale to purchase
        if potion_color_str not in sorted_catalog:
            print(f"Wanted to buy some {potion_color_str} barrels, but there are none for sale at this time :(")
            continue #just move onto the next potion type

        select_catalog = sorted_catalog[potion_color_str]
        #print(f'Select Catalog: {select_catalog}')

        current_request, inventory_gold = balance_requests(priority[i], select_catalog, inventory_gold)
        request_barrels.extend(current_request)
        print(f"Requesting {request_barrels}")
        print(f"Inventory Gold: {inventory_gold}")

    print(f'Requesting Barrels: \n{request_barrels}')
    
    return request_barrels

#current purchasing logic: maximize purchase of top priority
def balance_requests(current_priority, select_catalog, inventory_gold):
    request = []
    request_quantity = 0
    total_request_ml = 0
    current_ml_in_barrel = current_priority[2]
    max_inventory_ml = 2500 - current_ml_in_barrel
    for barrel in select_catalog:
        #usually first items are largest available to smallest
        safe_request = []
        safe_request.append(barrel.quantity) #the max amount of barrels available
        safe_request.append(inventory_gold//barrel.price) #the max barrels we can purchase
        safe_request.append(max_inventory_ml//barrel.ml_per_barrel) #max mls reached
        request_quantity = min(safe_request) #the lowest we can purchase

        if request_quantity > 0: # add the request if exists
            request.append(
                {"sku": barrel.sku,
                 "quantity": request_quantity}
                 )
            #update inventory_ml
            inventory_gold -= (request_quantity*barrel.price)
            total_request_ml += request_quantity*barrel.ml_per_barrel
            max_inventory_ml -= total_request_ml
    
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
