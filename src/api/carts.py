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

# cart_id = 0
# carts = {}

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    # global cart_id
    # global carts
    # cart_id += 1
    new_cart_sql = """INSERT INTO carts 
                        (customer_name)
                        VALUES (:name)
                        RETURNING cart_id"""
    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text(new_cart_sql), [{"name": new_cart.customer}]).scalar_one()
    print(f"Cart_ID added: {cart_id}")
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
    #basic logic
    #check where the item sku matches in potion_catalog
    #insert it into the database with the cart_id and potion_id, and quantity, sku
    #if the current number is greater than the inventory, then just give it the max of the inventory

    print("Setting Item Quantity...")
    with db.engine.begin() as connection:
        # potion_inventory = connection.execute(sqlalchemy.text("SELECT * \
        #                                                       FROM potion_catalog\
        #                                                       WHERE item_sku = :item_sku"), 
        #                                                       [{"item_sku": item_sku}]).one()

        insert_items_sql = """INSERT INTO cart_items (cart_id, potion_id, quantity, sku)
                            SELECT :cart_id, potion_catalog.id, :quantity, :item_sku
                            FROM potion_catalog WHERE potion_catalog.sku = :item_sku"""
        

        connection.execute(sqlalchemy.text(insert_items_sql), 
                           [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])

        # potion_info = connection.execute(sqlalchemy.text("""SELECT id
        #                                                     FROM potion_catalog
        #                                                     WHERE sku = :item_sku"""), 
        #                                                     [{"item_sku": item_sku}]).one()

        # connection.execute(sqlalchemy.text("""INSERT INTO cart_items (cart_id, potion_id, quantity, sku)
        #                                     VALUES( :cart_id, :potion_id, :quantity, :sku)"""),
        #                                     [{"cart_id": cart_id, "potion_id": potion_info.id, "quantity": cart_item.quantity, "sku": item_sku}])

    print(f"Successfully added {cart_item.quantity} {item_sku} for Cart {cart_id}")
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    gold_paid = 0
    print(f"Checkout for {cart_id}:")
    with db.engine.begin() as connection:
        #go into the cart_items and filter out all the items that are from the current cart
        cart_items = connection.execute(sqlalchemy.text("""SELECT * 
                                                        FROM cart_items
                                                        WHERE cart_id = :cart_id"""), 
                                                        [{"cart_id": cart_id}]).all()
        print(f"Cart Items: {cart_items}")
        #make sure potion_inventory matches, if not give the max
        for item in cart_items:
            print(f"Item: {item}")
            #find the general potion id inventory
            
            #get potion inventory
            potion_quant = connection.execute(sqlalchemy.text("""SELECT sum(change) as quantity
                                                FROM potions_ledger
                                                WHERE potion_id = :potion_id"""),
                                               [{"potion_id": item.potion_id}]).one()
            # potion_info = connection.execute(sqlalchemy.text("""SELECT quantity, price
            #                                                     FROM potion_catalog
            #                                                     WHERE id = :potion_id"""), 
            #                                                     [{"potion_id": item.potion_id}]).one()
            
            #if the requested cart item's quantity is greater than our inventory, set inventory max
            if item.quantity > potion_quant.quantity:
                connection.execute(sqlalchemy.text("""UPDATE cart_items
                                                    SET quantity = :inventory_quant
                                                    WHERE cart_id = :cart_id and potion_id = :potion_id"""), 
                                                    [{"cart_id": cart_id, "potion_id": item.potion_id,
                                                      "inventory_quant": potion_quant.quantity}])
            #start checkout 
            #update gold, potions bought, checkout completed

            price = connection.execute(sqlalchemy.text("""SELECT price
                                                        FROM potion_catalog
                                                        WHERE id = :potion_id"""), 
                                                        [{"potion_id": item.potion_id}]).one()

            #updating potions bought (-)
            description = f"{cart_id} bought {item.quantity} {item.sku}"
            connection.execute(sqlalchemy.text("""INSERT INTO potions_ledger (potion_id, change, description)
                                                    VALUES (:potion_id, :change, :description)"""), 
                                                    [{"potion_id": item.potion_id, "change": -item.quantity, "description": description}])
            
            
            #update gold paid
            gold_paid = price.price * item.quantity
            description = f"{cart_id} bought {item.quantity} {item.sku} for {gold_paid}"
            connection.execute(sqlalchemy.text("""INSERT INTO gold_inventory (change, description)
                                                    VALUES (:change, :description)"""), 
                                                    [{"change": -gold_paid, "description": description}])
            
            
            #update checkout for item
            connection.execute(sqlalchemy.text("""UPDATE cart_items
                                                    SET checkout_complete = true
                                                    WHERE cart_id = :cart_id and potion_id = :potion_id"""), 
                                                    [{"potion_id": item.potion_id, "cart_id": cart_id}])
            
            print(f"Cart {cart_id} bought {item.quantity} {item.sku} for {gold_paid}")

            
    print("Checkout Complete.")
    return "OK"
