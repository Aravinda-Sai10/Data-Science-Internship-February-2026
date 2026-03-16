from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi import HTTPException


app = FastAPI()

# DATA STORAGE

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 799, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "USB Cable", "price": 199, "category": "Electronics", "in_stock": False},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False},
]

cart = []
order_history = []
feedback = []
orders = []

# MODELS


class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)


class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)


class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]

class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True


# BASIC ROUTES
# 

@app.get("/")
def home():
    return {"message": "Welcome to my store API"}

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


# DAY 1 ENDPOINTS


@app.get("/products/instock")
def get_instock():
    available = [p for p in products if p["in_stock"]]
    return {"in_stock_products": available, "count": len(available)}


@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):

    result = [p for p in products if p["category"].lower() == category_name.lower()]

    if not result:
        return {"error": "No products found in this category"}

    return {"category": category_name, "products": result, "total": len(result)}


@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not results:
        return {"message": "No products matched your search"}

    return {
        "keyword": keyword,
        "results": results,
        "total_matches": len(results)
    }


@app.get("/products/deals")
def get_deals():

    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }


@app.get("/store/summary")
def store_summary():

    in_stock_count = len([p for p in products if p["in_stock"]])
    out_stock_count = len(products) - in_stock_count

    categories = list(set(p["category"] for p in products))

    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_stock_count,
        "categories": categories
    }

# DAY 2 ENDPOINTS

@app.get("/products/filter")
def filter_products(
    category: str = Query(None),
    min_price: int = Query(None),
    max_price: int = Query(None)
):

    result = products

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    return {"products": result, "total": len(result)}


@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    return {"error": "Product not found"}


@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback)
    }


@app.get("/products/summary")
def product_summary():

    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])

    categories = list(set(p["category"] for p in products))

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {
            "name": expensive["name"],
            "price": expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": categories
    }


@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})

        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})

        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

# BONUS ORDER TRACKER

@app.post("/orders")
def place_order(product_id: int, quantity: int):

    order = {
        "order_id": len(orders) + 1,
        "product_id": product_id,
        "quantity": quantity,
        "status": "pending"
    }

    orders.append(order)

    return {"message": "Order placed successfully", "order": order}


@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}

    return {"error": "Order not found"}


@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"

            return {"message": "Order confirmed", "order": order}

    return {"error": "Order not found"}
    
# Dayv 3 ENDPOINTS
@app.post("/products")
def add_product(product: NewProduct):

    for p in products:
        if p["name"].lower() == product.name.lower():
            return {"error":"Product already exists"}

    new_id = max(p["id"] for p in products) + 1

    new_product = {
        "id": new_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock
    }

    products.append(new_product)

    return {
        "message":"Product added",
        "product":new_product
    }

@app.put("/products/discount")
def discount(category:str,discount_percent:int):

    updated=[]

    for p in products:

        if p["category"]==category:

            p["price"]=int(
                p["price"]*(1-discount_percent/100)
            )

            updated.append(p)

    if not updated:

        return {"message":"No products found"}

    return{

        "message":"Discount applied",

        "updated":len(updated),

        "products":updated
    }

@app.put("/products/{product_id}")
def update_product(
    product_id:int,
    price:int=None,
    in_stock:bool=None
):

    for product in products:

        if product["id"]==product_id:

            if price is not None:
                product["price"]=price

            if in_stock is not None:
                product["in_stock"]=in_stock

            return {"message":"Product updated","product":product}

    return {"error":"Product not found"}

@app.get("/products/audit")
def product_audit():

    in_stock=[p for p in products if p["in_stock"]]

    out_stock=[p for p in products if not p["in_stock"]]

    total_value=sum(p["price"]*10 for p in in_stock)

    expensive=max(products,key=lambda p:p["price"])

    return{

        "total_products":len(products),

        "in_stock_count":len(in_stock),

        "out_of_stock_names":[p["name"] for p in out_stock],

        "total_stock_value":total_value,

        "most_expensive":{
            "name":expensive["name"],
            "price":expensive["price"]
        }

    }

@app.delete("/products/{product_id}")
def delete_product(product_id:int):

    for product in products:

        if product["id"]==product_id:

            products.remove(product)

            return {
                "message":f"Product '{product['name']}' deleted"
            }

    return {"error":"Product not found"}



def calculate_total(product, quantity):
    return product["price"] * quantity

# ADD TO CART
@app.post("/cart/add")
def add_to_cart(product_id:int, quantity:int=1):

    product = next((p for p in products if p["id"]==product_id),None)

    if not product:
        raise HTTPException(status_code=404,detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(
            status_code=400,
            detail=f"{product['name']} is out of stock"
        )

    for item in cart:

        if item["product_id"]==product_id:

            item["quantity"]+=quantity

            item["subtotal"]=calculate_total(product,item["quantity"])

            return{
                "message":"Cart updated",
                "cart_item":item
            }

    new_item={

        "product_id":product_id,
        "product_name":product["name"],
        "quantity":quantity,
        "unit_price":product["price"],
        "subtotal":calculate_total(product,quantity)
    }

    cart.append(new_item)

    return{
        "message":"Added to cart",
        "cart_item":new_item
    }

# VIEW CART
@app.get("/cart")
def view_cart():

    if not cart:
        return {"message":"Cart is empty"}

    grand_total=sum(item["subtotal"] for item in cart)

    return{

        "items":cart,

        "item_count":len(cart),

        "grand_total":grand_total
    }

# REMOVE ITEM
@app.delete("/cart/{product_id}")
def remove_item(product_id:int):

    for item in cart:

        if item["product_id"]==product_id:

            cart.remove(item)

            return{
                "message":"Item removed",
                "removed":item["product_name"]
            }

    return {"error":"Item not found"}

# CHECKOUT MODEL
class Checkout(BaseModel):

    customer_name:str

    delivery_address:str

# CHECKOUT
@app.post("/cart/checkout")
def checkout(data:Checkout):

    if not cart:

        raise HTTPException(
            status_code=400,
            detail="Cart is empty — add items first"
        )

    grand_total=sum(item["subtotal"] for item in cart)

    new_orders=[]

    for item in cart:

        order={

            "order_id":len(order_history)+1,

            "customer_name":data.customer_name,

            "product":item["product_name"],

            "quantity":item["quantity"],

            "total_price":item["subtotal"],

            "address":data.delivery_address
        }

        order_history.append(order)

        new_orders.append(order)

    cart.clear()

    return{

        "message":"Checkout successful",

        "orders_placed":new_orders,

        "grand_total":grand_total
    }

# ORDERS
@app.get("/orders")
def get_orders():

    return{

        "orders":order_history,

        "total_orders":len(order_history)
    }