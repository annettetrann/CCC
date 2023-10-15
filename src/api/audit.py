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

        get_sql = f'SELECT *\
        FROM global_inventory'

        result = connection.execute(sqlalchemy.text(get_sql)).one()

        num_potions = result.num_red_potion + result.num_green_potion + result.num_blue_potion
        num_barrel_ml = result.num_red_ml + result.num_green_ml + result.num_blue_ml
        gold = result.gold
        
    return {"number_of_potions": num_potions, "ml_in_barrels": num_barrel_ml, "gold": gold}

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
