from etl.database import DatabaseManager

db = DatabaseManager()
try:
    # Check what tables exist
    result = db.execute_query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    print("Tables in database:")
    for row in result:
        print(f"  - {row[0]}")
    
    # Check columns in projeto_status table
    result = db.execute_query("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'projeto_status'
        ORDER BY ordinal_position
    """)
    print("\nColumns in projeto_status table:")
    for row in result:
        print(f"  - {row[0]} ({row[1]})")
        
except Exception as e:
    print(f"Error: {e}")
