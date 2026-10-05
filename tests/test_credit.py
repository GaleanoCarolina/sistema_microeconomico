from repositories.product_repository import ProductRepository
from repositories.customer_repository import CustomerRepository
from services.sales_service import SalesService
from services.credit_service import CreditService

def test_partial_credit_and_payment(db):
    p=ProductRepository(db); c=CustomerRepository(db); pid=p.add('Arroz',None,5,10,10); cid=c.add('Juan',credit_limit=200)
    sale=SalesService(db).create_sale([{'product_id':pid,'quantity':2}],'PARTIAL',cid,5)
    assert sale['total_cents']==2000 and sale['paid_cents']==500 and sale['credit_cents']==1500
    cs=CreditService(db); assert cs.customer_balance_cents(cid)==1500
    new=cs.add_payment(cid,10); assert new==500

def test_reject_overpayment(db):
    p=ProductRepository(db); c=CustomerRepository(db); pid=p.add('Pan',None,2,5,10); cid=c.add('Ana')
    SalesService(db).create_sale([{'product_id':pid,'quantity':1}],'CREDIT',cid,0)
    try: CreditService(db).add_payment(cid,10); assert False
    except ValueError: pass
