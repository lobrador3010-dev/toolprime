from app.database import SessionLocal, engine
from app import models

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

cats = [
    models.Category(name="Дрели и перфораторы", slug="dreli"),
    models.Category(name="Шлифовальные машины", slug="shlifovka"),
    models.Category(name="Пилы и лобзики", slug="pily"),
    models.Category(name="Измерительные приборы", slug="izmerenie"),
]
for c in cats:
    db.add(c)
db.commit()

brands = [
    models.Brand(name="Bosch", slug="bosch"),
    models.Brand(name="Makita", slug="makita"),
    models.Brand(name="DeWalt", slug="dewalt"),
    models.Brand(name="Hilti", slug="hilti"),
]
for b in brands:
    db.add(b)
db.commit()

products = [
    models.Product(name="Дрель Bosch GSB 13 RE", slug="bosch-gsb-13", price=4990, old_price=5990, category_id=1, brand_id=1, in_stock=True),
    models.Product(name="Перфоратор Makita HR2470", slug="makita-hr2470", price=12500, old_price=14000, category_id=1, brand_id=2, in_stock=True),
    models.Product(name="УШМ DeWalt DWE4157", slug="dewalt-dwe4157", price=8900, old_price=None, category_id=2, brand_id=3, in_stock=True),
    models.Product(name="Лобзик Bosch PST 700 E", slug="bosch-pst700", price=5200, old_price=6100, category_id=3, brand_id=1, in_stock=True),
    models.Product(name="Перфоратор Hilti TE 30", slug="hilti-te30", price=32000, old_price=None, category_id=1, brand_id=4, in_stock=False),
    models.Product(name="Лазерный уровень Bosch GLL 3-80", slug="bosch-gll380", price=18700, old_price=21000, category_id=4, brand_id=1, in_stock=True),
    models.Product(name="Шлифмашина Makita BO5041", slug="makita-bo5041", price=7300, old_price=8500, category_id=2, brand_id=2, in_stock=True),
    models.Product(name="Пила циркулярная DeWalt DWE550", slug="dewalt-dwe550", price=11200, old_price=None, category_id=3, brand_id=3, in_stock=True),
]
for p in products:
    db.add(p)
db.commit()
db.close()
print("Готово! Товары добавлены.")