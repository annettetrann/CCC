from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        
        potions = connection.execute(sqlalchemy.text("""SELECT sum(change) as quantity
                                                FROM potions_ledger""")).one()
        # sql_global = f'SELECT *\
        gold = connection.execute(sqlalchemy.text("""SELECT sum(change) as gold
                                                FROM gold_inventory""")).one()
        barrels = connection.execute(sqlalchemy.text("""SELECT sum(change) as quantity
                                                FROM barrels_ledger""")).one()
        #     FROM global_inventory'
        # get_global = connection.execute(sqlalchemy.text(sql_global)).one()
        
        # #get number of potions
        # num_potions = 0
        # sql_potions = f'SELECT quantity\
        #             FROM potion_catalog'
        # potions = connection.execute(sqlalchemy.text(sql_potions)).all()
        # print(f"Potions: {potions}")

        # for potions in potions:
        #     num_potions += potions.quantity
        # num_barrel_ml = get_global.num_red_ml + get_global.num_green_ml + get_global.num_blue_ml + get_global.num_dark_ml
        # gold = get_global.gold
        
    return {"number_of_potions": potions.quantity, "ml_in_barrels": barrels.quantity, "gold": gold.gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
