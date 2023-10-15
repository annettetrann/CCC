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
    #if cart is not yet created, create it
    if (cart_id not in carts):
        carts[cart_id] = {}
    current_cart = carts[cart_id]

    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).one()

    red_inventory = result.num_red_potion
    green_inventory = result.num_green_potion
    blue_inventory = result.num_blue_potion

    #check enough inventory, if not enough give max in inventory
    #check each sku 
    if (item_sku == "RED_POTION"):
        if (cart_item.quantity > red_inventory):
            current_cart[item_sku] = red_inventory
        else:
            current_cart[item_sku] = cart_item.quantity 
    elif (item_sku == "GREEN_POTION"):
        if (cart_item.quantity > green_inventory):
            current_cart[item_sku] = green_inventory
        else:
            current_cart[item_sku] = cart_item.quantity 
    elif (item_sku == "BLUE_POTION"):
        if (cart_item.quantity > blue_inventory):
            current_cart[item_sku] = blue_inventory
        else:
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
    total_red_potions_bought = 0
    total_green_potions_bought = 0
    total_blue_potions_bought = 0

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).one()
        current_quant_red = result.num_red_potion
        current_quant_green = result.num_green_potion
        current_quant_blue = result.num_blue_potion

    for item_sku, quantity in curr_cart.items():
        if quantity > 0:
            if item_sku == "RED_POTION":
                if (quantity > current_quant_red):
                    quantity = current_quant_red
                total_red_potions_bought += quantity
            elif item_sku == "GREEN_POTION":
                if (quantity > current_quant_green):
                    quantity = current_quant_green
                total_green_potions_bought += quantity
            elif item_sku == "BLUE_POTION":
                if (quantity > current_quant_blue):
                    quantity = current_quant_blue
                total_blue_potions_bought += quantity
            total_gold_paid += (quantity*50) # each potion is $50
    
                
    with db.engine.begin() as connection:
        update_sql = """UPDATE global_inventory
                        SET num_red_potion = num_red_potion - :total_red_potions_bought,
                        num_green_potion = num_green_potion - :total_green_potions_bought,
                        num_blue_potion = num_blue_potion - :total_blue_potions_bought,
                        gold = gold + :total_gold_paid"""
        connection.execute(sqlalchemy.text(update_sql), 
                        [{"total_red_potions_bought": total_red_potions_bought, 
                            "total_green_potions_bought": total_green_potions_bought,
                            "total_blue_potions_bought": total_blue_potions_bought,
                            "total_gold_paid": total_gold_paid}])
    print(f"Checkout for {cart_id}:\
          {total_red_potions_bought} red potions,\
          {total_green_potions_bought} green potions,\
          {total_blue_potions_bought} blue potions,\
          total gold paid = {total_gold_paid}")
    
    return "OK"