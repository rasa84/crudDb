import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="dmo_shop"
)

c = conn.cursor()


def print_info():
    print(" --------------------------------------------")
    print("1. Prekių atvaizdavimas")
    print("2. Naujos prekės įkėlimas")
    print("3. Prekės redagavimas")
    print("4. Prekės šalinimas")
    print("5. Prekės pirkimas")
    print("6. Populiariausia prekė")
    print("7. Daugiausiai pelno sugeneravusi prekė")
    print("8. Ataskaita periode")
    print("9. Įšaldyti pinigai")
    print("10. Būsima pardaviminė vertė")
    print("11. Prognozuojamas pelnas viską išpardavus")
    print("12. Išeiti iš programos")
    print(" --------------------------------------------")


def print_items(result):
    print("***************************************************************************")
    headers = ["ID", "Pavadinimas", "Gamintojo kaina", "Pardavimo kaina", "Kiekis"]
    row_format = "{0:<6} | {1:<15} | {2:>15} | {3:>15} | {4:>10} |"
    print(row_format.format(*headers))
    for r in result:
        data = [r[0], r[1], r[2], r[3], r[4]]
        print(row_format.format(*data))
    print("***************************************************************************")


def get_items():
    query = "select * from items"
    c.execute(query)
    return c.fetchall()


def get_item(item_id):
    query = "select * from items where id = " + str(item_id)
    c.execute(query)
    res = c.fetchone()
    return dict(
        id=res[0],
        title=res[1],
        manufacturer_price=res[2],
        sale_price=res[3],
        quantity=res[4]
    )


def add_item():
    title = input("Prekės pavadinimas: ")
    m_price = input("Tiekėjo kaina: ")
    s_price = input("Pardavimo kaina: ")
    quantity = input("Prekių kiekis: ")
    query = f"INSERT INTO `items` (`title`, `manufacturer_price`, `sale_price`, `quantity`) VALUES (%s, %s, %s, %s)"
    c.execute(query, (title, m_price, s_price, quantity))
    conn.commit()


def edit_item():
    item_id = input("Pasirinkite prekės, kurią redaguosite, id: ")
    item = get_item(item_id)
    print(item)
    title = input("Prekės pavadinimas: ") or item['title']
    m_price = input("Tiekėjo kaina: ") or item['manufacturer_price']
    s_price = input("Pardavimo kaina: ") or item['sale_price']
    quantity = input("Prekių kiekis: ") or item['quantity']
    query = f"UPDATE `items` SET `title`=%s, `manufacturer_price`=%s, `sale_price`=%s, `quantity`=%s WHERE `id`=%s"
    c.execute(query, (title, m_price, s_price, quantity, item_id))
    conn.commit()


def delete_item():
    item_id = input("Pasirinkite prekės, kurią norite pašalinti, id: ")
    query = "DELETE FROM `items` WHERE `id`=%s"
    c.execute(query, (item_id,))
    conn.commit()


def buy_item():
    item_id = int(input("Pasirinkite prekės, kurią pirksite, id: "))
    item = get_item(item_id)
    quantity = int(input("Pasirinkite kiekį: "))
    while True:
        if item['quantity'] < quantity:
            print("Nepakankamas prekių likutis")
            quantity = int(input("Pasirinkite kiekį: "))
        else:
            break

    query1 = f"UPDATE `items` SET `quantity`=%s WHERE `id`=%s"
    c.execute(query1, (item['quantity'] - quantity, item_id))
    query2 = (
        "INSERT INTO `payments`( `item_id`, `quantity`, `manufacturer_price`, `sale_price_per_unit`, `created_at` ) "
        "VALUES(%s, %s, %s, %s, "
        "'2024-12-31' - INTERVAL FLOOR(RAND() * 1095) DAY + "
        "INTERVAL FLOOR(RAND() * 23) HOUR + "
        "INTERVAL FLOOR(RAND() * 59) MINUTE + "
        "INTERVAL FLOOR(RAND() * 59) SECOND )")
    c.execute(query2, (item_id, quantity, item['manufacturer_price'], item['sale_price']))
    conn.commit()


def print_most_popular_item():
    query = ("SELECT i.title, SUM(p.quantity) AS quant FROM `payments` p JOIN items i ON i.id = p.item_id "
             "GROUP BY `item_id` HAVING quant =(SELECT SUM(p.quantity) AS quant FROM `payments` p JOIN items i "
             "ON i.id = p.item_id GROUP BY `item_id` ORDER BY quant DESC LIMIT 1)")
    c.execute(query)
    res = c.fetchone()
    print(f"Populiariausia prekė: {res[0]}")


def print_most_profitable_item():
    query = ("SELECT i.title, SUM(profit) AS total_profit FROM "
             "(SELECT id, item_id, quantity * (sale_price_per_unit - manufacturer_price) AS profit FROM `payments`) p "
             "JOIN items i ON i.id = p.item_id GROUP BY item_id HAVING total_profit ="
             "(SELECT SUM(profit) AS total_profit FROM (SELECT id, item_id, quantity * (sale_price_per_unit - manufacturer_price) "
             "AS profit FROM `payments` ) p "
             "GROUP BY item_id ORDER BY total_profit DESC LIMIT 1)")
    c.execute(query)
    res = c.fetchone()
    print(f"Daugiausiai pelno sugeneravusi prekė: {res[0]}")


def print_annual_report():
    year = int(input("Įveskite metus: "))
    query = ("SELECT YEAR(created_at) AS YEAR, MONTH(created_at) AS month, SUM(quantity) AS items_sold_per_month, "
             "SUM(income) AS month_income, SUM(profit) AS month_profit FROM "
             "(SELECT created_at, quantity, quantity * sale_price_per_unit AS income, "
             "quantity *( sale_price_per_unit - manufacturer_price) AS profit FROM `payments`) p "
             "WHERE YEAR(created_at) = %s GROUP BY YEAR(created_at), MONTH(created_at)")
    c.execute(query, (year,))
    result = c.fetchall()
    months = ('sausis', 'vasaris', 'kovas', 'balandis', 'gegužė', 'birželis',
              'liepa', 'rugpjūtis', 'rugsėjis', 'spalis', 'lapkritis', 'gruodis')
    print("*******************************************************************")
    print(f"{result[0][0]}-ųjų metų ataskaita: ")
    print("*******************************************************************")
    headers = ["Mėnesis", "Iš viso parduota", "Pajamos", "Pelnas"]
    row_format = "{0:<15} | {1:>20} | {2:>10} | {3:>10} |"
    print(row_format.format(*headers))
    for r in result:
        data = [months[r[1] - 1], r[2], r[3], r[4]]
        print(row_format.format(*data))
    print("*******************************************************************")


def print_frozen_money():
    query = "SELECT sum(manufacturer_price * quantity) as frozen_money FROM `items`"
    c.execute(query)
    res = c.fetchone()
    print(f"Įšaldyti pinigai: {res[0]}")


def get_annual_income(year):
    query = ("SELECT YEAR(created_at) AS year, SUM(income) AS year_income FROM "
             "(SELECT created_at, quantity, quantity * sale_price_per_unit AS income FROM `payments`) p "
             "WHERE YEAR(created_at) = %s GROUP BY YEAR(created_at) ORDER BY YEAR(created_at)")
    c.execute(query, (year,))
    res = c.fetchone()
    return res[1]


def print_future_sale_value():
    year = int(input("Įveskite metus: "))
    current_year_income = get_annual_income(year - 1)
    last_year_income = get_annual_income(year - 2)
    growth_rate = (current_year_income - last_year_income) / last_year_income * 100
    future_sale_val = round(current_year_income * (1 + growth_rate / 100), 2)
    print(f"Būsima pardaviminė vertė: {future_sale_val}")


def print_projected_profit():
    query = "SELECT SUM((sale_price - manufacturer_price) * quantity ) FROM `items`"
    c.execute(query)
    res = c.fetchone()
    print(f"Prognozuojamas pelnas viską išpardavus: {res[0]}")


while True:
    print_info()
    opt = input()

    match opt:
        case '1':
            items = get_items()
            print_items(items)
        case '2':
            add_item()
        case '3':
            edit_item()
        case '4':
            delete_item()
        case '5':
            buy_item()
        case '6':
            print_most_popular_item()
        case '7':
            print_most_profitable_item()
        case '8':
            print_annual_report()
        case '9':
            print_frozen_money()
        case '10':
            print_future_sale_value()
        case '11':
            print_projected_profit()
        case '12':
            exit(1)
