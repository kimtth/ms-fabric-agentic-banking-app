"""
Generate realistic sample banking data for OLTP/OLTAP/OLAP demo.
Inserts users, accounts, and transactions into Fabric SQL database.
"""
from datetime import datetime, timedelta
from pathlib import Path
from random import choice, randint, uniform
from typing import List, Tuple

from dotenv import load_dotenv
from sqlalchemy import text

# Load environment early
load_dotenv()  # Load from current working directory
load_dotenv(Path(__file__).with_name(".env"))  

from app.db import get_session  # noqa: E402


# Sample data pools
FIRST_NAMES = ["John", "Jane", "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
               "Isabella", "Jack", "Kate", "Liam", "Mia", "Noah", "Olivia", "Peter", "Quinn", "Rachel"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Martinez", "Lopez",
              "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "White", "Harris"]

ACCOUNT_TYPES = ["checking", "savings"]
ACCOUNT_NAMES = {
    "checking": ["Primary Checking", "Everyday Checking", "Joint Checking", "Business Checking", "Student Checking", "Main Checking"],
    "savings": ["High-Yield Savings", "Emergency Fund", "Vacation Savings", "Retirement Savings", "College Fund", "Rainy Day Fund"]
}

TRANSACTION_CATEGORIES = {
    "Groceries": ["Grocery Store", "Supermarket", "Farmer's Market", "Whole Foods"],
    "Food": ["Restaurant", "Coffee Shop", "Fast Food", "Dinner", "Lunch", "Breakfast Cafe"],
    "Transportation": ["Gas Station", "Public Transit", "Uber", "Parking", "Auto Service"],
    "Housing": ["Rent Payment", "Mortgage", "HOA Fees", "Property Tax"],
    "Utilities": ["Electric Bill", "Water Bill", "Gas Bill", "Internet Service", "Phone Bill"],
    "Shopping": ["Clothing Store", "Electronics Store", "Online Shopping", "Department Store"],
    "Health": ["Pharmacy", "Doctor Visit", "Gym Membership", "Health Insurance"],
    "Education": ["Bookstore", "Tuition Payment", "School Supplies", "Online Course"],
    "Entertainment": ["Movie Theater", "Concert Tickets", "Streaming Service", "Gaming"],
    "Transfer": ["Monthly Savings", "Account Transfer", "Emergency Fund Transfer"],
    "Income": ["Paycheck", "Bonus", "Freelance Payment", "Investment Return", "Gift"]
}


def generate_users(count: int = 20) -> List[Tuple[str, str, str]]:
    """Generate user records."""
    users = []
    for i in range(1, count + 1):
        user_id = f"user_{i}"
        first = choice(FIRST_NAMES)
        last = choice(LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{i if i > 1 else ''}@example.com"
        users.append((user_id, name, email))
    return users


def generate_accounts(users: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str, str, float, str]]:
    """Generate 2-3 accounts per user."""
    accounts = []
    acc_num_seed = 123456789
    
    for user_id, name, _ in users:
        num_accounts = randint(2, 3)
        for i in range(num_accounts):
            acc_id = f"acc_{len(accounts) + 1}"
            acc_number = str(acc_num_seed + len(accounts))
            acc_type = choice(ACCOUNT_TYPES)
            acc_name = choice(ACCOUNT_NAMES[acc_type])
            
            # Realistic balance ranges
            if acc_type == "checking":
                balance = round(uniform(500, 8000), 2)
            else:  # savings
                balance = round(uniform(2000, 20000), 2)
            
            accounts.append((acc_id, user_id, acc_number, acc_type, balance, acc_name))
    
    return accounts


def generate_transactions(accounts: List[Tuple[str, str, str, str, float, str]], count: int = 200) -> List[dict]:
    """Generate realistic transactions over the past 90 days."""
    transactions = []
    base_date = datetime.now() - timedelta(days=90)
    
    for i in range(1, count + 1):
        tx_id = f"txn_{i}"
        
        # Random timestamp within past 90 days
        days_offset = randint(0, 90)
        hours_offset = randint(0, 23)
        minutes_offset = randint(0, 59)
        created_at = base_date + timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset)
        
        # 60% payments, 30% transfers, 10% deposits
        tx_type_roll = randint(1, 100)
        
        if tx_type_roll <= 60:  # Payment
            from_acc = choice(accounts)
            from_account_id = from_acc[0]
            to_account_id = None
            tx_type = "payment"
            category = choice(list(TRANSACTION_CATEGORIES.keys()))
            if category == "Transfer" or category == "Income":
                category = "Shopping"  # Avoid these for payments
            description = choice(TRANSACTION_CATEGORIES[category])
            
            # Payment amounts by category
            if category in ["Groceries", "Food", "Health"]:
                amount = round(uniform(15, 200), 2)
            elif category in ["Transportation", "Shopping", "Entertainment"]:
                amount = round(uniform(20, 500), 2)
            elif category in ["Housing", "Utilities"]:
                amount = round(uniform(50, 2000), 2)
            else:
                amount = round(uniform(10, 300), 2)
        
        elif tx_type_roll <= 90:  # Transfer
            from_acc = choice(accounts)
            # Try to find another account from same user
            same_user_accounts = [a for a in accounts if a[1] == from_acc[1] and a[0] != from_acc[0]]
            if same_user_accounts:
                to_acc = choice(same_user_accounts)
            else:
                to_acc = choice([a for a in accounts if a[0] != from_acc[0]])
            
            from_account_id = from_acc[0]
            to_account_id = to_acc[0]
            tx_type = "transfer"
            category = "Transfer"
            description = choice(TRANSACTION_CATEGORIES["Transfer"])
            amount = round(uniform(100, 2000), 2)
        
        else:  # Deposit
            to_acc = choice(accounts)
            from_account_id = None
            to_account_id = to_acc[0]
            tx_type = "deposit"
            category = "Income"
            description = choice(TRANSACTION_CATEGORIES["Income"])
            amount = round(uniform(500, 5000), 2)
        
        status = choice(["posted", "pending", "completed"])
        
        transactions.append({
            "id": tx_id,
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": amount,
            "type": tx_type,
            "description": description,
            "category": category,
            "status": status,
            "created_at": created_at.isoformat()
        })
    
    return transactions


def insert_data():
    """Insert generated data into database."""
    print("🔄 Generating sample data...")
    
    # Generate data
    users = generate_users(count=20)
    accounts = generate_accounts(users)
    transactions = generate_transactions(accounts, count=200)
    
    print(f"✅ Generated {len(users)} users, {len(accounts)} accounts, {len(transactions)} transactions")
    
    # Insert into database
    with get_session() as session:
        print("\n🔄 Inserting users...")
        for user_id, name, email in users:
            session.execute(
                text("INSERT INTO dbo.users (id, name, email) VALUES (:id, :name, :email)"),
                {"id": user_id, "name": name, "email": email}
            )
        print(f"✅ Inserted {len(users)} users")
        
        print("\n🔄 Inserting accounts...")
        for acc_id, user_id, acc_number, acc_type, balance, acc_name in accounts:
            session.execute(
                text(
                    "INSERT INTO dbo.accounts (id, user_id, account_number, account_type, balance, name) "
                    "VALUES (:id, :user_id, :account_number, :account_type, :balance, :name)"
                ),
                {
                    "id": acc_id,
                    "user_id": user_id,
                    "account_number": acc_number,
                    "account_type": acc_type,
                    "balance": balance,
                    "name": acc_name
                }
            )
        print(f"✅ Inserted {len(accounts)} accounts")
        
        print("\n🔄 Inserting transactions...")
        for tx in transactions:
            session.execute(
                text(
                    "INSERT INTO dbo.transactions "
                    "(id, from_account_id, to_account_id, amount, type, description, category, status, created_at) "
                    "VALUES (:id, :from_account_id, :to_account_id, :amount, :type, :description, :category, :status, :created_at)"
                ),
                tx
            )
        print(f"✅ Inserted {len(transactions)} transactions")
    
    print("\n✨ Sample data generation complete!")



def clear_data():
    """Clear existing data (useful for re-running the script)."""
    print("🗑️  Clearing existing data...")
    
    with get_session() as session:
        session.execute(text("DELETE FROM dbo.transactions"))
        session.execute(text("DELETE FROM dbo.accounts"))
        session.execute(text("DELETE FROM dbo.users"))
    
    print("✅ Data cleared")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_data()
    else:
        print("🚀 Starting sample data generation...")
        print("   (Use --clear to remove existing data first)\n")
        
        # Check if data already exists
        with get_session() as session:
            count = session.execute(text("SELECT COUNT(*) FROM dbo.users")).scalar()
            if count > 0:
                print(f"⚠️  Warning: {count} users already exist. Use --clear to remove existing data.")
                confirm = input("Continue anyway? (y/N): ")
                if confirm.lower() != 'y':
                    print("❌ Aborted")
                    sys.exit(0)
        
        insert_data()
