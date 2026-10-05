from utils.dates import iso_date
class FEFOService:
    @staticmethod
    def eligible_lots(con,product_id):
        today=iso_date()
        return con.execute('''SELECT * FROM lots WHERE product_id=? AND quantity_remaining>0 AND status='ACTIVE'
          AND (expiry_date IS NULL OR expiry_date>=?)
          ORDER BY CASE WHEN expiry_date IS NULL THEN 1 ELSE 0 END,expiry_date ASC,received_at ASC,id ASC''',(product_id,today)).fetchall()
    @staticmethod
    def expired_lots(con,product_id=None):
        today=iso_date()
        if product_id:return con.execute('SELECT * FROM lots WHERE product_id=? AND quantity_remaining>0 AND expiry_date IS NOT NULL AND expiry_date<? ORDER BY expiry_date,id',(product_id,today)).fetchall()
        return con.execute('SELECT * FROM lots WHERE quantity_remaining>0 AND expiry_date IS NOT NULL AND expiry_date<? ORDER BY expiry_date,id',(today,)).fetchall()
