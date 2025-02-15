from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from itertools import permutations

app = FastAPI()

# Definiujemy model danych dla API
class Product(BaseModel):
    name: str
    regular_price: float
    discount_price: float

# Rabaty na najtańszy produkt w zależności od ilości produktów w koszyku
discounts = {2: 0.30, 3: 0.55, 4: 0.80, 5: 0.99}

# Funkcja do obliczania kosztu zamówienia
def calculate_order_price(order):
    if len(order) < 2:
        return sum(p.discount_price for p in order)  # Bez rabatu przy 1 produkcie

    min_price_regular = min(p.regular_price for p in order)  # Najtańszy produkt (cena regularna)
    discount = discounts.get(len(order), 0)  # Pobieramy rabat dla danej liczby produktów

    total_price = sum(p.discount_price for p in order)  # Cena po kodach rabatowych
    discount_value = min_price_regular * discount  # Rabat na najtańszy produkt

    final_price = total_price - discount_value  # Końcowa cena po rabacie

    # **NAPRAWA**: Zapobiegamy błędom JSON (NaN, inf)
    if final_price < 0 or not isinstance(final_price, (int, float)) or final_price != final_price:
        final_price = 0

    return final_price

# Funkcja do znajdowania optymalnego podziału zamówień
def find_best_split(products):
    best_split = []
    best_total_cost = float('inf')

    # Szukamy podziału na 2-4 zamówienia
    for num_orders in range(2, 5):
        for perm in permutations(products):
            split = [list(perm[i::num_orders]) for i in range(num_orders)]

            # Każde zamówienie musi mieć min. 2 produkty i max. 5
            if all(2 <= len(order) <= 5 for order in split):
                total_cost = sum(calculate_order_price(order) for order in split)

                if total_cost < best_total_cost:
                    best_total_cost = total_cost
                    best_split = split

    return best_split, best_total_cost

# API endpoint do obliczania rabatu
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

    return {
        "orders": result,
        "total_price": best_total_cost
    }