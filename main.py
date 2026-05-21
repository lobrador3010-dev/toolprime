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
    return templates.TemplateResponse(request=request, name="index.html", context={
        "categories": categories, "products": products, "active_page": "home",
    })

@app.get("/cart")
async def cart(request: Request):
    return templates.TemplateResponse(request=request, name="cart.html", context={"active_page": "cart"})

@app.get("/services")
async def services(request: Request):
    return templates.TemplateResponse(request=request, name="services.html", context={"active_page": "services"})

@app.get("/edo")
async def edo(request: Request):
    return templates.TemplateResponse(request=request, name="edo.html", context={"active_page": "edo"})

@app.get("/delivery")
async def delivery(request: Request):
    return templates.TemplateResponse(request=request, name="delivery.html", context={"active_page": "delivery"})

@app.get("/contacts")
async def contacts(request: Request):
    return templates.TemplateResponse(request=request, name="contacts.html", context={"active_page": "contacts"})

@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse(request=request, name="about.html", context={"active_page": "about"})

@app.get("/requisites")
async def requisites(request: Request):
    return templates.TemplateResponse(request=request, name="requisites.html", context={"active_page": "requisites"})
