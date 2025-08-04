import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

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

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Customer API",
    description="A RESTful API to provide customer data and basic order statistics.",
    version="1.0.0"
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

@app.get("/customers", response_model=PaginatedCustomerResponse, tags=["Customers"])
def list_customers(
    page: int = Query(1, ge=1, description="The page number to retrieve."),
    per_page: int = Query(10, ge=1, le=100, description="The number of customers per page.")
):
    """
    Retrieves a paginated list of all customers.
    """
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
    """
    Retrieves details for a specific customer by their ID, including their total order count.
    """
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

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Customer API!"}
