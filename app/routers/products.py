from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/product/{slug}")
async def product_page(slug: str, request: Request, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    related = db.query(models.Product).filter(
        models.Product.category_id == product.category_id,
        models.Product.id != product.id
    ).limit(6).all()
    breadcrumb = []
    cat = product.category
    if cat:
        if cat.parent:
            breadcrumb.append(cat.parent)
        breadcrumb.append(cat)
    return templates.TemplateResponse(request=request, name="product.html", context={
        "product": product, "related": related, "breadcrumb": breadcrumb,
    })
