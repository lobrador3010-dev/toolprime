from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import engine, get_db, Base
from app import models

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    categories = db.query(models.Category).all()
    products = db.query(models.Product).limit(12).all()
    brands = db.query(models.Brand).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"categories": categories, "products": products, "brands": brands}
    )

@app.get("/catalog")
async def catalog(
    request: Request,
    db: Session = Depends(get_db),
    category: str = None,
    brand: str = None,
    in_stock: bool = None,
    min_price: float = None,
    max_price: float = None,
    q: str = None
):
    query = db.query(models.Product)

    if category:
        query = query.join(models.Category).filter(models.Category.slug == category)
    if brand:
        brands_list = brand.split(",")
        query = query.join(models.Brand).filter(models.Brand.slug.in_(brands_list))
    if in_stock:
        query = query.filter(models.Product.in_stock == True)
    if min_price:
        query = query.filter(models.Product.price >= min_price)
    if max_price:
        query = query.filter(models.Product.price <= max_price)
    if q:
        query = query.filter(models.Product.name.ilike(f"%{q}%"))

    products = query.all()
    categories = db.query(models.Category).all()
    brands = db.query(models.Brand).all()
    total = len(products)

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "products": products,
            "categories": categories,
            "brands": brands,
            "total": total,
            "selected_category": category,
            "selected_brand": brand,
            "in_stock": in_stock,
            "min_price": min_price,
            "max_price": max_price,
            "q": q
        }
    )

from fastapi import HTTPException

@app.get("/product/{slug}")
async def product_page(slug: str, request: Request, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    related = db.query(models.Product).filter(
        models.Product.category_id == product.category_id,
        models.Product.id != product.id
    ).limit(4).all()
    return templates.TemplateResponse(
        request=request,
        name="product.html",
        context={"product": product, "related": related}
    )