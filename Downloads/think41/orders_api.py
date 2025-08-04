#  milestone 2
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Configuration ---
DB_NAME = 'ecommerce.db'

# --- Pydantic Models (for data validation and response shaping) ---
class Customer(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    age: int
    gender: str
    state: str
    street_address: str
    postal_code: str
    city: str
    country: str
    latitude: float
    longitude: float
    traffic_source: str
    created_at: str

class CustomerWithOrderCount(Customer):
    order_count: int

class PaginatedCustomerResponse(BaseModel):
    page: int
    per_page: int
    total_customers: int
    total_pages: int
    data: List[Customer]

class Order(BaseModel):
    order_id: int
    user_id: int
    status: str
    gender: str
    created_at: str
    returned_at: Optional[str] = None
    shipped_at: Optional[str] = None
    delivered_at: Optional[str] = None
    num_of_item: int

# --- FastAPI App Initialization ---
app = FastAPI(
    title="E-commerce API",
    description="A RESTful API for customer and order data.",
    version="1.1.0"
)

# Enable CORS to allow frontend applications to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Database Helper Function ---
def get_db_connection():
    """Creates and returns a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

# --- API Endpoints ---

@app.get("/", tags=["Health Check"])
def read_root():
    """A simple health check endpoint."""
    return {"status": "ok", "message": "Welcome to the E-commerce API!"}

# --- Customer Endpoints ---

@app.get("/customers", response_model=PaginatedCustomerResponse, tags=["Customers"])
def list_customers(
    page: int = Query(1, ge=1, description="The page number to retrieve."),
    per_page: int = Query(10, ge=1, le=100, description="The number of customers per page.")
):
    offset = (page - 1) * per_page
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    total_customers = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    customers_query = 'SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?'
    customers = cursor.execute(customers_query, (per_page, offset)).fetchall()
    conn.close()

    total_pages = (total_customers + per_page - 1) // per_page

    return {
        "page": page,
        "per_page": per_page,
        "total_customers": total_customers,
        "total_pages": total_pages,
        "data": [dict(row) for row in customers]
    }

@app.get("/customers/{user_id}", response_model=CustomerWithOrderCount, tags=["Customers"])
def get_customer_details(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    cursor = conn.cursor()
    customer = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer with ID {user_id} not found")

    order_count = cursor.execute('SELECT COUNT(*) FROM orders WHERE user_id = ?', (user_id,)).fetchone()[0]
    conn.close()

    customer_data = dict(customer)
    customer_data['order_count'] = order_count
    
    return customer_data

# --- Order Endpoints ---

@app.get("/customers/{user_id}/orders", response_model=List[Order], tags=["Orders"])
def get_orders_for_customer(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()

    customer = cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer with ID {user_id} not found")

    orders = cursor.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    conn.close()

    return [dict(row) for row in orders]

@app.get("/orders/{order_id}", response_model=Order, tags=["Orders"])
def get_order_details(order_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()

    order = cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)).fetchone()
    conn.close()

    if order is None:
        raise HTTPException(status_code=404, detail=f"Order with ID {order_id} not found")

    return dict(order)
