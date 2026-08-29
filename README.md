Handmade Bliss — Simple Inventory-style Products API

Overview
- SQLite + SQLAlchemy backend
- FastAPI HTTP API
- GET /api/products                -> list products (optional category, pagination)
- GET /api/products/{category}     -> list products in one category, for example gifts
- POST /api/products               -> create a product and return the saved product

How to use
1. Install dependencies:
   pip install -r requirements.txt

2. Run the app:
   uvicorn main:app --reload

3. Open docs:
   http://127.0.0.1:8000/docs

Quick curl examples
- List:
  curl "http://127.0.0.1:8000/api/products"

- Create:
  curl -X POST "http://127.0.0.1:8000/api/products" -H "Content-Type: application/json" \
    -d '{"name":"Handmade Mug","description":"Ceramic mug","price":12.5,"category":"kitchen","stock":10}'

Exact JSON payload
```json
{
  "name": "Handmade Mug",
  "description": "Ceramic mug",
  "price": 12.5,
  "category": "kitchen",
  "image_url": "https://example.com/handmade-mug.jpg",
  "stock": 10
}
```

Frontend POST request
```js
async function createProduct(productData) {
  const response = await fetch("http://127.0.0.1:8000/api/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(productData)
  });

  if (!response.ok) {
    throw new Error("Unable to create product");
  }

  return response.json();
}

async function handleProductSubmit(formValues) {
  const createdProduct = await createProduct({
    name: formValues.name,
    description: formValues.description,
    price: Number(formValues.price),
    category: formValues.category,
    image_url: formValues.image_url || null,
    stock: Number(formValues.stock || 0)
  });

  setProducts((currentProducts) =>
    createdProduct.category === activeCategory
      ? [...currentProducts, createdProduct]
      : currentProducts
  );
}
```

The category must come from the form or application state; it must not be hardcoded.
For a category page, load products with `GET /api/products/{category}` or
`GET /api/products?category={category}`. The created product is returned by the POST
response, so adding it to the current list makes it appear immediately in its category.

- Set stock:
  curl -X PUT "http://127.0.0.1:8000/api/products/1/stock" -H "Content-Type: application/json" \
    -d '{"stock":42}'