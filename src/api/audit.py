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
        gold = connection.execute(sqlalchemy.text("""SELECT sum(change) as gold
                                                FROM gold_inventory""")).one()
        barrels = connection.execute(sqlalchemy.text("""SELECT sum(change) as quantity
                                                FROM barrels_ledger""")).one()
        
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
