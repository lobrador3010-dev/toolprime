from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import engine, get_db, Base
from app import models
from app.routers import catalog as catalog_router
from app.routers import products as products_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title="ToolPrime", version="2.0.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
app.include_router(catalog_router.router)
app.include_router(products_router.router)

@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    categories = db.query(models.Category).filter(models.Category.parent_id == None).order_by(models.Category.name).all()
    products = db.query(models.Product).filter(models.Product.in_stock == True).order_by(models.Product.id.desc()).limit(12).all()
    brands = db.query(models.Brand).join(models.Product).distinct().order_by(models.Brand.name).all()
    return templates.TemplateResponse(request=request, name="index.html", context={
        "categories": categories, "products": products, "brands": brands,
    })

@app.get("/cart")
async def cart(request: Request):
    return templates.TemplateResponse(request=request, name="cart.html", context={})
