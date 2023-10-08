from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
import logging
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
            if (barrel.sku == "SMALL_RED_BARREL"):
                print(f'Puchased {barrel.quantity} of {barrel.sku}({barrel.ml_per_barrel}ml)')
                
                total_red_ml = result.num_red_ml + (barrel.quantity*barrel.ml_per_barrel)
                print(f'Total red ml added: {(barrel.quantity*barrel.ml_per_barrel)}')
                print(f'Updated total red_ml available now: {total_red_ml}')

                total_gold = result.gold - (barrel.quantity*barrel.price)
                print(f'Total purchase price: {barrel.quantity*barrel.price},\
                      Updated gold = {total_gold}')
    
        #update db with upated values
        update_sql = f'UPDATE global_inventory\
                                           SET num_red_ml = {total_red_ml},\
                                           gold = {total_gold}'
        
        connection.execute(sqlalchemy.text(update_sql))


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("BARREL PLAN: ")

    print(f'Wholesale catalog: {wholesale_catalog}')

    update_sql = "SELECT * \
        FROM global_inventory"
    
    request_redBarrel = 0
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(update_sql)).one()

        print("Inventory Red Potions: "+ str(result.num_red_potion))
        print("Inventory Gold: "+ str(result.gold))

        #if number of red potions is less than 10 and we have enough money , buy a barrel. 
        for barrel in wholesale_catalog:
            print(f'Barrel: {barrel}')
            if(barrel.sku == 'SMALL_RED_BARREL'):
                if ((result.num_red_potion < 10) and (result.gold >= barrel.price)):
                    print(f'less than 10 red potions!, it is currently: {result.num_red_potion}')
                    request_redBarrel += 1
                    print(f'requesting {request_redBarrel} red barrels.')

    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": request_redBarrel,
        }
    ]
