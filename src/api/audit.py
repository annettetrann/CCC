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
    
        return {"num_red_potion": result.num_red_potion, 
                "num_red_ml": result.num_red_ml,
                "num_green_potion": result.num_green_potion, 
                "num_green_ml": result.num_green_ml,
                "num_blue_potion": result.num_blue_potion, 
                "num_blue_ml": result.num_blue_ml,
                "gold": result.gold}

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
