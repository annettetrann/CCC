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
    print("BOTTLE DELIVERY: ")
    red_potion = [100, 0, 0, 0]
    green_potion = [0, 100, 0, 0]
    update_num_red_potion = 0
    update_num_red_ml = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT *\
                                                                FROM global_inventory")).one()
        for potion in potions_delivered:
            print(f"Current Potion: {potions_delivered}")
            print(f"green potion compare: {green_potion == potion.potion_type}")
            
            #checking red potion
            if (potion.potion_type == red_potion):
                update_num_red_potion = result.num_red_potion + potion.quantity
                #update db with upated values
                print(f'Adding {potion.quantity} red potions')

                #update amount of mls taken to bottle
                update_num_red_ml = result.num_red_ml - (potion.quantity*100)

                update_sql = f'UPDATE global_inventory\
                                                SET num_red_potion = {update_num_red_potion},\
                                                    num_red_ml = {update_num_red_ml}'
                
                connection.execute(sqlalchemy.text(update_sql))

                #make sure results are updated
                result = connection.execute(sqlalchemy.text("SELECT *\
                                                                FROM global_inventory")).one()
                print(f'RED_POTION: \n\
                      {(potion.quantity*100)}ml was used to make {potion.quantity} red potions.\n\
                      There are now {result.num_red_potion} red potions and {result.num_red_ml}ml left')


    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    print("BOTTLE PLAN: ")

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT *\
                                                              FROM global_inventory")).one()
        inventory_red_ml = result.num_red_ml
        #check available barrels available!


        #check greatest potions we can make
        #each potion bottle contains 100ml
        request_red_potions = inventory_red_ml//100
        print(f'Requesting {request_red_potions} red potions to be made')

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": request_red_potions
            }
        ]
