from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str

cart_id = 0
carts = {}

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    global cart_id
    global carts
    cart_id += 1

    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):

    """ """
    #store all the carts
    if (cart_id not in carts):
        carts[cart_id] = {}
    current_cart = carts[cart_id]
    current_cart[item_sku] = cart_item.quantity 
    print(f'Carts: {carts}')   
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    curr_cart = carts[cart_id]
    total_gold_paid = 0
    total_potions_bought = 0

    with db.engine.begin() as connection:
        get_sql = "SELECT gold \
        FROM global_inventory"
        result = connection.execute(sqlalchemy.text(get_sql)).one()
        print(f"Current Gold: {result.gold}")

        for item_sku, quantity in curr_cart.items():
            gold_paid = 0
            potions_bought = 0
            if item_sku == "RED_POTION":
                #update gold
                gold_paid += (quantity*50) # each potion is $50
                total_gold_paid += gold_paid
                #update num of potions
                potions_bought += quantity
                total_potions_bought += potions_bought
                # update database
                update_sql = "UPDATE global_inventory\
                        SET num_red_potions = num_red_potions - potions_bought\
                        gold = gold + {gold_paid}"
            elif item_sku == "GREEN_POTION":
                #update gold
                gold_paid += (quantity*50) # each potion is $50
                total_gold_paid += gold_paid
                #update num of potions
                potions_bought += quantity
                total_potions_bought += potions_bought
                # update database
                update_sql = "UPDATE global_inventory\
                        SET num_green_potions = num_green_potions - potions_bought\
                        gold = gold + {gold_paid}"
            elif item_sku == "BLUE_POTION":
                #update gold
                gold_paid += (quantity*50) # each potion is $50
                total_gold_paid += gold_paid
                #update num of potions
                potions_bought += quantity
                total_potions_bought += potions_bought
                # update database
                update_sql = "UPDATE global_inventory\
                        SET num_blue_potions = num_blue_potions - potions_bought\
                        gold = gold + {gold_paid}"
                
            print(f'Bought {potions_bought} {item_sku}, \n\
                      total = {gold_paid}')
            
        
    print(f'total_potions_bought: {total_potions_bought}, total_gold_paid: {total_gold_paid}')
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
