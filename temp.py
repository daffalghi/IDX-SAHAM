import sqlite3

conn = sqlite3.connect('IDX-API/data/database.sqlite')
cursor = conn.cursor()

# Get schemas for foreign_trading and stock_summary
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('foreign_trading', 'stock_summary')")
for row in cursor.fetchall():
    print(row[0])
    
# also get some rows from stock_summary to see the columns clearly
cursor.execute("SELECT * FROM stock_summary LIMIT 1")
print([description[0] for description in cursor.description])
