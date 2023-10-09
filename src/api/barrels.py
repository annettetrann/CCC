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

    with db.engine.begin() as connection:
        #returns an array I am trying to update
        result = connection.execute(sqlalchemy.text("SELECT *\
                                                              FROM global_inventory")).one()

        #add new amount of red potion to current inventory & update gold used
        total_gold = result.gold
        print(f'Inventory gold = {total_gold}')

        for barrel in barrels_delivered:
            print(f'Barrels Delivered: {barrel}')
            print(f'Puchased {barrel.quantity} of {barrel.sku}({barrel.ml_per_barrel}ml)')
            if (barrel.sku == "SMALL_RED_BARREL"):
                total_red_ml = result.num_red_ml + (barrel.quantity*barrel.ml_per_barrel)
                print(f'Total red ml added: {(barrel.quantity*barrel.ml_per_barrel)}')
                print(f'Updated total red_ml available now: {total_red_ml}')

                total_gold -= barrel.quantity*barrel.price
                print(f'Total purchase price: {barrel.quantity*barrel.price},\
                      Updated gold = {total_gold}')
                
            if (barrel.sku == "SMALL_GREEN_BARREL"): 
                total_green_ml = result.num_green_ml + (barrel.quantity*barrel.ml_per_barrel)
                print(f'Total green ml added: {(barrel.quantity*barrel.ml_per_barrel)}')
                print(f'Updated total green_ml available now: {total_green_ml}')

                total_gold -= barrel.quantity*barrel.price
                print(f'Total purchase price: {barrel.quantity*barrel.price},\
                      Updated gold = {total_gold}')
            if (barrel.sku == "SMALL_BLUE_BARREL"):
                total_blue_ml = result.num_blue_ml + (barrel.quantity*barrel.ml_per_barrel)
                print(f'Total blue ml added: {(barrel.quantity*barrel.ml_per_barrel)}')
                print(f'Updated total green_ml available now: {total_blue_ml}')

                total_gold -= barrel.quantity*barrel.price
                print(f'Total purchase price: {barrel.quantity*barrel.price},\
                      Updated gold = {total_gold}')
    
        #update db with upated values
        update_sql = f'UPDATE global_inventory\
                                           SET num_red_ml = {total_red_ml},\
                                            num_green_ml = {total_green_ml},\
                                            num_blue_ml = {total_blue_ml},\
                                            gold = {total_gold}'
        
        connection.execute(sqlalchemy.text(update_sql))


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("BARREL PLAN: ")

    print(f'Wholesale catalog: {wholesale_catalog}')

    barrels_to_buy = []    
    request_redBarrel = 0
    request_greenBarrel = 0
    request_blueBarrel = 0

    #check available barrels available!
    
    with db.engine.begin() as connection:
        get_sql = "SELECT * \
        FROM global_inventory"
        result = connection.execute(sqlalchemy.text(get_sql)).one()
        print(f"Inventory Gold: {result.gold}")

        inventory_gold = result.gold

        #if number of red potions is less than 10 and we have enough money , buy a barrel. 
        for barrel in wholesale_catalog:
            print(f'Barrel: {barrel}')
            if(barrel.sku == 'SMALL_RED_BARREL'):
                print("Inventory Red Potions: "+ str(result.num_red_potion))
                if ((result.num_red_potion < 10) and (inventory_gold >= barrel.price)):
                    print(f'less than 10 red potions!')
                    request_redBarrel += 1
                    print(f'requesting {request_redBarrel} red barrels: \n\
                          -${barrel.price*request_redBarrel} from {inventory_gold}')
                    inventory_gold -= barrel.price*request_redBarrel
                    barrels_to_buy.append(
                        {
                        "sku": "SMALL_RED_BARREL",
                        "quantity": request_redBarrel,
                        }
                    )
                
            if(barrel.sku == 'SMALL_GREEN_BARREL'):
                print("Inventory Green Potions: "+ str(result.num_green_potion))
                if ((result.num_green_potion < 10) and (inventory_gold >= barrel.price)):
                    print(f'less than 10 green potions!')
                    request_greenBarrel += 1
                    print(f'requesting {request_greenBarrel} green barrels: \n\
                          -${barrel.price*request_greenBarrel} from {inventory_gold}')
                    inventory_gold -= barrel.price*request_greenBarrel
                    barrels_to_buy.append(
                        {
                            "sku": "SMALL_GREEN_BARREL",
                            "quantity": request_greenBarrel,
                        }
                    )
            
            if(barrel.sku == 'SMALL_BLUE_BARREL'):
                print("Inventory Blue Potions: "+ str(result.num_blue_potion))
                if ((result.num_blue_potion < 10) and (inventory_gold >= barrel.price)):
                    print(f'less than 10 blue potions!')
                    request_blueBarrel += 1
                    print(f'requesting {request_blueBarrel} green barrels: \n\
                          -${barrel.price*request_blueBarrel} from {inventory_gold}')
                    inventory_gold -= barrel.price*request_blueBarrel
                    barrels_to_buy.append(
                        {
                        "sku": "SMALL_BLUE_BARREL",
                        "quantity": request_blueBarrel,
                        }
                    )
        

                
    #dont update databased because we havent confirmed the purchase
                
    print(f"Requesting: \n\
          {request_redBarrel} red barrels, \n\
          {request_greenBarrel} green barrels, \n\
          {request_blueBarrel} blue barrels")
    
    return barrels_to_buy
