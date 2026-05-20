from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
from app.database import get_db
from app import models

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
PAGE_SIZE = 48

@router.get("/catalog")
async def catalog(
    request: Request, db: Session = Depends(get_db),
    category: Optional[str] = None, brand: Optional[str] = None,
    in_stock: Optional[bool] = None, min_price: Optional[float] = None,
    max_price: Optional[float] = None, q: Optional[str] = None,
    sort: Optional[str] = "popular", page: int = 1,
):
    query = db.query(models.Product)
    if category:
        cat_obj = db.query(models.Category).filter(models.Category.slug == category).first()
        if cat_obj:
            child_ids = [c.id for c in cat_obj.children]
            query = query.filter(models.Product.category_id.in_([cat_obj.id] + child_ids))
    if brand:
        brand_slugs = [b.strip() for b in brand.split(",") if b.strip()]
        query = query.join(models.Brand).filter(models.Brand.slug.in_(brand_slugs))
    if in_stock:
        query = query.filter(models.Product.in_stock == True)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.Product.name.ilike(like), models.Product.sku.ilike(like)))
    if sort == "price_asc":
        query = query.order_by(models.Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(models.Product.price.desc())
    elif sort == "new":
        query = query.order_by(models.Product.id.desc())
    else:
        query = query.order_by(models.Product.id.asc())
    total = query.count()
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))
    products = query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
    categories = db.query(models.Category).filter(models.Category.parent_id == None).order_by(models.Category.name).all()
    brands_raw = db.query(models.Brand).join(models.Product).distinct().order_by(models.Brand.name).all()
    price_range = db.query(func.min(models.Product.price), func.max(models.Product.price)).first()
    global_min = int(price_range[0] or 0)
    global_max = int(price_range[1] or 100000)
    return templates.TemplateResponse(request=request, name="catalog.html", context={
        "products": products, "categories": categories, "brands": brands_raw,
        "total": total, "total_pages": total_pages, "page": page, "page_size": PAGE_SIZE,
        "selected_category": category, "selected_brand": brand, "in_stock": in_stock,
        "min_price": min_price, "max_price": max_price, "q": q, "sort": sort,
        "global_min": global_min, "global_max": global_max,
    })
