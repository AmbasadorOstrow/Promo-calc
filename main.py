from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from itertools import permutations
import math

app = FastAPI()

# ✅ CORS Middleware – pozwalamy na połączenia z GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model produktu
class Product(BaseModel):
    name: str
    regular_price: float
    discount_price: float

# Rabaty
discounts = {2: 0.30, 3: 0.55, 4: 0.80, 5: 0.99}

# ✅ Funkcja liczenia ceny - eliminacja `NaN` i `inf`
def calculate_order_price(order):
    if len(order) < 2:
        return sum(p.discount_price for p in order)

    min_price_regular = min(p.regular_price for p in order)
    discount = discounts.get(len(order), 0)

    total_price = sum(p.discount_price for p in order)
    discount_value = min_price_regular * discount
    final_price = total_price - discount_value  

    # 🛠️ **NAPRAWA**: Zabezpieczenie przed `NaN` i `inf`
    if math.isnan(final_price) or math.isinf(final_price) or final_price < 0:
        final_price = 0.0

    return final_price

# ✅ Funkcja znajdowania najlepszego podziału zamówienia
def find_best_split(products):
    best_split = []
    best_total_cost = float('inf')

    for num_orders in range(2, 5):
        for perm in permutations(products):
            split = [list(perm[i::num_orders]) for i in range(num_orders)]
            if all(2 <= len(order) <= 5 for order in split):
                total_cost = sum(calculate_order_price(order) for order in split)
                if not math.isinf(total_cost) and not math.isnan(total_cost):  # ✅ Eliminacja `inf`
                    if total_cost < best_total_cost:
                        best_total_cost = total_cost
                        best_split = split

    # 🛠️ **NAPRAWA**: Jeśli `best_total_cost` jest nadal `inf`, ustaw na 0
    if math.isinf(best_total_cost) or best_total_cost < 0:
        best_total_cost = 0.0

    return best_split, best_total_cost

# ✅ Endpoint API `/calculate`
@app.post("/calculate")
async def calculate_discount(products: list[Product]):
    if len(products) < 2:
        raise HTTPException(status_code=400, detail="Dodaj co najmniej 2 produkty!")

    best_orders, best_total_cost = find_best_split(products)

    result = []
    for i, order in enumerate(best_orders, start=1):
        result.append({
            "order": i,
            "products": [{"name": p.name, "regular_price": p.regular_price, "discount_price": p.discount_price} for p in order],
            "final_price": calculate_order_price(order)
        })

    response = JSONResponse(content={"orders": result, "total_price": best_total_cost})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response
