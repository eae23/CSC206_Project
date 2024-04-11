from flask import Flask, request, render_template, session, redirect, jsonify
import mariadb
import mariadb.cursors
import myDatabase as db
import sys

# Launch app and define where the static assets will be located
app = Flask(__name__, static_url_path='/assets')
app.secret_key = 'genevaauto-eae'

@app.route('/', methods=['GET', 'POST'])
def base():

    if not session.get('logged_in', None):
        session['logged_in'] = False

    if not session.get('role', None):
        session['role'] = ''

    return render_template('base.html')

@app.route('/vehicles', methods=['GET', 'POST'])
def all_vehicles():

    # Connect to MariaDB Platform
    try:
        conn=db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    # Execute Query
    cur.execute( "SELECT * from Vehicles")
    output = cur.fetchall()

    # Return to the browser - View template = listing.html with in-template variable = vehicles
    return render_template('vehicles/listing.html', vehicles=output, forsale=False)


@app.route('/vehicles_search', methods=['GET', 'POST'])
def vehicles_search():
    # Connect to MariaDB Platform
    try:
        conn = db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    # Execute Query to return vehicle_types
    cur.execute('''SELECT DISTINCT vehicle_type_name FROM vehicletypes
                    ORDER BY vehicle_type_name ASC''')
    vehicle_types = cur.fetchall()

    # Execute Query to return manufacturers
    cur.execute('''SELECT DISTINCT manufacturer_name FROM manufacturers
                    ORDER BY manufacturer_name ASC''')
    manufacturers = cur.fetchall()

    # Execute Query to return model_years
    cur.execute('''SELECT DISTINCT model_year FROM vehicles
                    ORDER BY model_year ASC''')
    model_years = cur.fetchall()

    # Execute Query to return fuel_types
    cur.execute('''SELECT DISTINCT fuel_type FROM vehicles
                    ORDER BY fuel_type ASC''')
    fuel_types = cur.fetchall()

    # Execute Query to return colors
    cur.execute('''SELECT DISTINCT color_name FROM colors
                    ORDER BY color_name ASC''')
    color_names = cur.fetchall()

    return render_template('vehicles_search.html',
                           vehicle_types=vehicle_types, manufacturers=manufacturers, model_years=model_years,
                           fuel_types=fuel_types, color_names=color_names)


@app.route('/vehicles_search_results', methods=['GET', 'POST'])
def vehicles_search_results():
    vehicle_type = request.form.get("vehicle_type", None)
    manufacturer = request.form.get("manufacturer", None)
    model_year = request.form.get("model_year", None)
    fuel_type = request.form.get("fuel_type", None)
    color_name = request.form.get("color_name", None)

    # Connect to MariaDB Platform
    try:
        conn=db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    if session['logged_in']:
        if session['role'] == 'Owner':
            forsaleonly = False
            cur.execute('''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name,
                            (CASE nvl(pt.purchase_price, 0)
                             WHEN 0 THEN '' 
                             ELSE FORMAT(ROUND((pt.purchase_price * 1.4) + nvl(p.parts_cost, 0), 2), 2)
                             END
                            ) AS sales_price,   
                            GROUP_CONCAT(DISTINCT c.color_name) color,
                            (SELECT 'Y'
                              FROM vehicles v2
                              WHERE v2.vehicleID = v.vehicleID
                              AND v2.vehicleID NOT IN (SELECT vehicleID FROM purchasetransactions)) AS available_to_buy
                    FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, vehicles v
                        LEFT JOIN purchasetransactions pt ON v.vehicleID = pt.vehicleID
                        LEFT JOIN partorders po ON v.vehicleID = po.vehicleID
                        LEFT JOIN (SELECT part_orderID, (SUM(cost * quantity) * 1.2 ) AS parts_cost 
                                    FROM parts 
                                    GROUP BY part_orderID) p 
                            ON po.part_orderID = p.part_orderID
                                    WHERE v.vehicle_typeID = vt.vehicle_typeID
                                         AND m.manufacturerID = v.manufacturerID
                                         AND v.vehicleID = vc.vehicleID
                                         AND vc.colorID = c.colorID
                                         AND (%s = '' OR vt.vehicle_type_name = %s)
                                         AND (%s = '' OR m.manufacturer_name = %s)
                                         AND (%s = '' OR v.model_year = %s)
                                         AND (%s = '' OR v.fuel_type = %s)
                                         AND (%s = '' OR c.color_name = %s)
                                   GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name
                                   ORDER BY v.model_year DESC, m.manufacturer_name ASC''', (
                vehicle_type, vehicle_type, manufacturer, manufacturer, model_year, model_year, fuel_type, fuel_type,
                color_name, color_name))

        else:   # Not an owner - Display only unsold vehicles
            forsaleonly = True

            cur.execute('''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name,
                            (CASE nvl(pt.purchase_price, 0)
                             WHEN 0 THEN '' 
                             ELSE FORMAT(ROUND((pt.purchase_price * 1.4) + nvl(p.parts_cost, 0), 2), 2)
                             END
                            ) AS sales_price,
                            GROUP_CONCAT(DISTINCT c.color_name) color, 
                            (SELECT 'Y'
                              FROM vehicles v2
                              WHERE v2.vehicleID = v.vehicleID
                              AND v2.vehicleID NOT IN (SELECT vehicleID FROM purchasetransactions)) AS available_to_buy
                    FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, vehicles v
                        LEFT JOIN purchasetransactions pt ON v.vehicleID = pt.vehicleID
                        LEFT JOIN partorders po ON v.vehicleID = po.vehicleID
                        LEFT JOIN (SELECT part_orderID, (SUM(cost * quantity) * 1.2 ) AS parts_cost 
                                    FROM parts 
                                    GROUP BY part_orderID) p 
                            ON po.part_orderID = p.part_orderID
                                    WHERE v.vehicle_typeID = vt.vehicle_typeID
                                         AND m.manufacturerID = v.manufacturerID
                                         AND v.vehicleID = vc.vehicleID
                                         AND vc.colorID = c.colorID
                                         AND (%s = '' OR vt.vehicle_type_name = %s)
                                         AND (%s = '' OR m.manufacturer_name = %s)
                                         AND (%s = '' OR v.model_year = %s)
                                         AND (%s = '' OR v.fuel_type = %s)
                                         AND (%s = '' OR c.color_name = %s)
                                    AND
                                        v.vehicleID NOT IN (SELECT vehicleID FROM salestransactions)
                                        and v.vehicleID NOT IN (
                                            SELECT DISTINCT vehicleID
                                            FROM partorders po
                                            INNER JOIN parts p on po.part_orderID = p.part_orderID
                                            WHERE p.`status` != 'Installed')
                                   GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name
                                   ORDER BY v.model_year DESC, m.manufacturer_name ASC''', (
                vehicle_type, vehicle_type, manufacturer, manufacturer, model_year, model_year, fuel_type, fuel_type,
                color_name, color_name))

    else:  # Not logged in - Public user - Display only unsold vehicles
        forsaleonly = True

        cur.execute( '''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name,
            FORMAT(ROUND((pt.purchase_price * 1.4) + nvl(p.parts_cost, 0),2),2) AS sales_price,
            GROUP_CONCAT(DISTINCT c.color_name) color, 
            'N' AS available_to_buy
    FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, purchasetransactions pt, vehicles v
        LEFT JOIN partorders po ON v.vehicleID = po.vehicleID
        LEFT JOIN (SELECT part_orderID, (SUM(cost * quantity) * 1.2 ) AS parts_cost 
                    FROM parts 
                    GROUP BY part_orderID) p 
            ON po.part_orderID = p.part_orderID
                    WHERE v.vehicle_typeID = vt.vehicle_typeID
                         AND m.manufacturerID = v.manufacturerID
                         AND v.vehicleID = vc.vehicleID
                         AND vc.colorID = c.colorID
                         AND pt.vehicleID = v.vehicleID
                         AND (%s = '' OR vt.vehicle_type_name = %s)
                         AND (%s = '' OR m.manufacturer_name = %s)
                         AND (%s = '' OR v.model_year = %s)
                         AND (%s = '' OR v.fuel_type = %s)
                         AND (%s = '' OR c.color_name = %s)
                    AND
                        v.vehicleID NOT IN (SELECT vehicleID FROM salestransactions)
                        and v.vehicleID NOT IN (
                            SELECT DISTINCT vehicleID
                            FROM partorders po
                            INNER JOIN parts p on po.part_orderID = p.part_orderID
                            WHERE p.`status` != 'Installed')
                   GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name
                   ORDER BY v.model_year DESC, m.manufacturer_name ASC''', (vehicle_type, vehicle_type, manufacturer, manufacturer, model_year, model_year, fuel_type, fuel_type, color_name, color_name))

    output = cur.fetchall()

    # Return to the browser - View template = listing.html with in-template variable = vehicles
    return render_template('vehicles/listing.html', vehicles=output, forsale=forsaleonly)

@app.route('/details', methods=['GET', 'POST'])
def details():
    if "vehicleID" in request.form:
        vehicle_id = int(request.form['vehicleID'])

    # Connect to MariaDB Platform
    try:
        conn = db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    # Check if user clicked Install button to install part from Details page
    if "installPartID" in request.form:
        part_id = int(request.form['installPartID'])
        vehicle_id = int(request.form['partVehicleID'])

        # Update part record to set status to Installed
        cur.execute('''UPDATE parts p 
                              SET p.status = 'Installed'
                            WHERE p.partID = %s''',
                    (part_id,))
        conn.commit()

    # Execute Query
    cur.execute('''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description,
                   (CASE nvl(pt.purchase_price, 0)
                     WHEN 0 THEN '' 
                     ELSE FORMAT(ROUND((pt.purchase_price * 1.4) + nvl(p.parts_cost, 0), 2), 2)
                     END
                    ) AS sales_price,   
                    GROUP_CONCAT(DISTINCT c.color_name) color,
                    (SELECT (CASE nvl(v2.vin, 'N') WHEN 'N' THEN 'N' ELSE 'Y' END) 
                        FROM vehicles v2
                        WHERE v2.vehicleID = v.vehicleID
                        AND v2.vehicleID NOT IN (SELECT vehicleID FROM salestransactions)
                        AND v2.vehicleID NOT IN (
                            SELECT DISTINCT vehicleID
                            FROM partorders po
                            INNER JOIN parts p on po.part_orderID = p.part_orderID
                            WHERE p.`status` != 'Installed')) ready_to_sell
                    FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, vehicles v
                        LEFT JOIN purchasetransactions pt ON v.vehicleID = pt.vehicleID
                        LEFT JOIN partorders po ON v.vehicleID = po.vehicleID
                        LEFT JOIN (SELECT part_orderID, (SUM(cost * quantity) * 1.2 ) AS parts_cost 
                                    FROM parts 
                                    GROUP BY part_orderID) p 
                            ON po.part_orderID = p.part_orderID
                            WHERE v.vehicle_typeID = vt.vehicle_typeID
                             AND m.manufacturerID = v.manufacturerID
                             AND v.vehicleID = vc.vehicleID
                             AND vc.colorID = c.colorID
                             AND v.vehicleID = %s
                           GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description''', (vehicle_id, ))
    vehicle = cur.fetchone()

    cur.execute('''SELECT
                      p.partID,
                      p.part_number,
                      p.description,
                      p.quantity,
                      p.cost,
                      p.status
                    FROM
                      parts p,
                      partorders po
                    WHERE
                      p.part_orderID = po.part_orderID
                      AND po.vehicleID = %s
               ORDER BY p.part_number ASC''',
                (vehicle_id,))
    parts = cur.fetchall()

    cur.execute('''SELECT
                      CONCAT(c.first_name, ' ', c.last_name) Name,
                      CONCAT(c.street, ', ', c.city, ', ', c.state, '  ', c.postal_code) Address,
                      c.phone_number Phone,
                      c.email_address Email
                    FROM
                      customers c,
                      purchasetransactions pt
                    WHERE
                      c.customerID = pt.customerID
                      AND pt.vehicleID = %s''',
                (vehicle_id,))
    seller = cur.fetchone()

    cur.execute('''SELECT
                      CONCAT(c.first_name, ' ', c.last_name) Name,
                      CONCAT(c.street, ', ', c.city, ', ', c.state, '  ', c.postal_code) Address,
                      c.phone_number Phone,
                      c.email_address Email
                    FROM
                      customers c,
                      salestransactions st
                    WHERE
                      c.customerID = st.customerID
                      AND st.vehicleID = %s''',
                (vehicle_id,))
    buyer = cur.fetchone()

    return render_template('vehicles/details.html', vehicle=vehicle, parts=parts, seller=seller, buyer=buyer)

@app.route('/sales_productivity', methods=['GET', 'POST'])
def sales_productivity():

    # Connect to MariaDB Platform
    try:
        conn=db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    # Execute Query
    cur.execute( '''SELECT
                      a.SalesPerson,
                      SUM(a.VehiclesSold) VehiclesSold,
                      FORMAT(SUM(a.SalesPrice), 2) TotalSales,
                      FORMAT(SUM(a.SalesPrice) / SUM(a.VehiclesSold), 2) AvgSale
                    FROM
                      (
                        SELECT
                          CONCAT(u.first_name, ' ', u.last_name) SalesPerson,
                          1 VehiclesSold,
                          ROUND((pt.purchase_price * 1.4), 2) SalesPrice
                        FROM
                          users u,
                          salestransactions st,
                          purchasetransactions pt,
                          vehicles v
                        WHERE
                          u.userID = st.userID
                          AND st.vehicleID = v.vehicleID
                          AND pt.vehicleID = v.vehicleID
                          AND u.role = 'Sales'
                        UNION
                        SELECT
                          CONCAT(u.first_name, ' ', u.last_name) SalesPerson,
                          0 VehiclesSold,
                          ROUND(((p.cost * quantity) * 1.2), 2) SalesPrice
                        FROM
                          users u,
                          salestransactions st,
                          purchasetransactions pt,
                          vehicles v,
                          partorders po,
                          parts p
                        WHERE
                          u.userID = st.userID
                          AND st.vehicleID = v.vehicleID
                          AND pt.vehicleID = v.vehicleID
                          AND v.vehicleID = po.vehicleID
                          AND po.part_orderID = p.part_orderID
                          AND u.role = 'Sales'
                      ) a
                    GROUP BY
                      SalesPerson
                    ORDER BY
                      VehiclesSold DESC,
                      TotalSales DESC''')
    output = cur.fetchall()

    # Return to the browser - View template = listing.html with in-template variable = vehicles
    return render_template('reports/sales_productivity.html', sales=output)


@app.route('/seller_history', methods=['GET', 'POST'])
def seller_history():

    # Connect to MariaDB Platform
    try:
        conn=db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    # Execute Query
    cur.execute( '''SELECT
                      CONCAT(c.first_name, ' ', c.last_name) Seller,
                      COUNT(v.vehicleID) VehiclesSold,
                      FORMAT(SUM(pt.purchase_price), 2) TotalSales
                    FROM
                      customers c,
                      purchasetransactions pt,
                      vehicles v
                    WHERE
                      c.customerID = pt.customerID
                      AND pt.vehicleID = v.vehicleID
                    GROUP BY
                      Seller
                    ORDER BY
                      VehiclesSold DESC,
                      TotalSales ASC''')
    output = cur.fetchall()

    # Return to the browser - View template = listing.html with in-template variable = vehicles
    return render_template('reports/seller_history.html', sales=output)


@app.route('/part_statistics', methods=['GET', 'POST'])
def part_statistics():

    # Connect to MariaDB Platform
    try:
        conn=db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    # Execute Query
    cur.execute( '''SELECT
                      v.vendor_name Vendor,
                      SUM(p.quantity) TotalPartsPurchased,
                      FORMAT(SUM(p.cost * p.quantity), 2) TotalPartsCost,
                      FORMAT(AVG(p.cost * p.quantity), 2) AvgPartsCost
                    FROM
                      vendors v,
                      partorders po,
                      parts p
                    WHERE
                      v.vendorID = po.vendorID
                      AND p.part_orderID = po.part_orderID
                    GROUP BY
                      Vendor
                    ORDER BY
                      TotalPartsPurchased DESC,
                      TotalPartsCost DESC''')
    output = cur.fetchall()

    # Return to the browser - View template = listing.html with in-template variable = vehicles
    return render_template('reports/part_statistics.html', sales=output)


@app.route('/buy', methods=['GET', 'POST'])
def buy():
    # Connect to MariaDB Platform
    try:
        conn = db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    vehicle_id = None
    if "buyVehicleID" in request.form:
        vehicle_id = int(request.form['buyVehicleID'])
        session['buyVehicleID'] = vehicle_id
        customer_id = None

    # Execute Query
    cur.execute('''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description,
                    (CASE nvl(pt.purchase_price, 0)
                     WHEN 0 THEN '' 
                     ELSE FORMAT(ROUND((pt.purchase_price * 1.4) + nvl(p.parts_cost, 0), 2), 2)
                     END
                    ) AS sales_price,   
                    GROUP_CONCAT(DISTINCT c.color_name) color
                    FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, vehicles v
                        LEFT JOIN purchasetransactions pt ON v.vehicleID = pt.vehicleID
                        LEFT JOIN partorders po ON v.vehicleID = po.vehicleID
                        LEFT JOIN (SELECT part_orderID, (SUM(cost * quantity) * 1.2 ) AS parts_cost 
                                    FROM parts 
                                    GROUP BY part_orderID) p 
                            ON po.part_orderID = p.part_orderID
                            WHERE v.vehicle_typeID = vt.vehicle_typeID
                             AND m.manufacturerID = v.manufacturerID
                             AND v.vehicleID = vc.vehicleID
                             AND vc.colorID = c.colorID
                             AND v.vehicleID = %s
                           GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description''',
                (vehicle_id,))
    vehicle = cur.fetchone()

    # Execute Query
    cur.execute('''SELECT c.customerID, c.first_name, c.last_name
                    FROM customers c
                    ORDER BY c.last_name ASC, c.first_name ASC''')
    customers = cur.fetchall()

    cur.execute('''SELECT u.userID, u.last_name, u.first_name
                    FROM users u
                    WHERE u.role = 'Sales'
                    ORDER BY u.last_name ASC, u.first_name ASC''')
    salespeople = cur.fetchall()

    return render_template('buy.html', customers=customers, salespeople=salespeople,
                           vehicle=vehicle, customer_id=customer_id)


@app.route("/save_customer", methods=["POST", "GET"])
def save_customer():
    # Connect to MariaDB Platform
    try:
        conn = db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        business_name = request.form['business_name']
        phone = request.form['phone']
        email = request.form['email']
        street = request.form['street']
        city = request.form['city']
        state = request.form['state']
        postal_code = request.form['postal_code']
        id_number = request.form['id_number']
        transaction_type = request.form['transaction_type']

        vehicle_id = None
        if transaction_type.upper() == 'BUY':
            vehicle_id = session['buyVehicleID']
        elif transaction_type.upper() == 'SELL':
            vehicle_id = session['sellVehicleID']

        cur.execute('''SELECT * FROM customers WHERE id_number = %s
                                OR (first_name = %s AND last_name = %s AND business_name = %s)''',
                            (id_number, first_name, last_name, business_name))

        # Check if match found - rowcount > 0 means customer already exists
        if cur.rowcount == 0:
            # Check that all required fields are not null
            if first_name and last_name and phone and street and city and state and postal_code and id_number:
                # Insert customer data into database
                try:
                    cur.execute('''INSERT INTO customers VALUES (
                                0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )''',
                                (phone, email, street, city, state, postal_code, id_number, first_name, last_name, business_name))
                    conn.commit()

                    cur.execute('''SELECT MAX(customerID) customerID FROM customers''')
                    new_customer = cur.fetchone()

                    customer_id = new_customer['customerID']
                except mariadb.Error as e:
                    print(f"Error inserting customer record: {e}")
        else:
            print(f"Customer already exists")

        cur.execute('''SELECT
                          c.customerID,
                          c.id_number,
                          c.first_name,
                          c.last_name,
                          c.business_name,
                          c.phone_number,
                          c.email_address,
                          c.street,
                          c.city,
                          c.state,
                          c.postal_code
                        FROM
                          customers c
                        ORDER BY
                            c.last_name ASC, 
                          c.first_name ASC,
                          c.business_name ASC''')
        customers = cur.fetchall()

        cur.execute('''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description,
                            (CASE nvl(pt.purchase_price, 0)
                             WHEN 0 THEN '' 
                             ELSE FORMAT(ROUND((pt.purchase_price * 1.4) + nvl(p.parts_cost, 0), 2), 2)
                             END
                            ) AS sales_price,   
                            GROUP_CONCAT(DISTINCT c.color_name) color
                        FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, vehicles v
                            LEFT JOIN purchasetransactions pt ON v.vehicleID = pt.vehicleID
                            LEFT JOIN partorders po ON v.vehicleID = po.vehicleID
                            LEFT JOIN (SELECT part_orderID, (SUM(cost * quantity) * 1.2 ) AS parts_cost 
                                        FROM parts 
                                        GROUP BY part_orderID) p 
                                ON po.part_orderID = p.part_orderID
                                WHERE v.vehicle_typeID = vt.vehicle_typeID
                                 AND m.manufacturerID = v.manufacturerID
                                 AND v.vehicleID = vc.vehicleID
                                 AND vc.colorID = c.colorID
                                 AND v.vehicleID = %s
                               GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description''',
                                (vehicle_id,))
        vehicle = cur.fetchone()

        if transaction_type.upper() == 'BUY':
            return render_template('buy.html', customers=customers, vehicle=vehicle, customer_id=customer_id)
        elif transaction_type.upper() == 'SELL':
            return render_template('sell.html', customers=customers, vehicle=vehicle, customer_id=customer_id)


@app.route('/process_purchase', methods=['GET', 'POST'])
def process_purchase():
    # Connect to MariaDB Platform
    try:
        conn = db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        customer_id = request.form['customer']
        salesperson_id = request.form['salesperson']
        purchase_date = request.form['purchase_date']
        purchase_price = request.form['purchase_price']
        vehicle_condition = request.form['vehicle_condition']

        vehicle_id = session['buyVehicleID']

        # Check that all required fields are not null
        #if customer_id and salesperson_id and purchase_date and purchase_price and vehicle_condition and vehicle_id:
        # Insert customer data into database
        try:
            cur.execute('''INSERT INTO purchasetransactions VALUES (
                            0, %s, %s, %s, %s, %s, %s
                            )''',
                        (vehicle_id, salesperson_id, customer_id, purchase_price, purchase_date, vehicle_condition))
            conn.commit()

        except mariadb.Error as e:
            # msg = "Error inserting customer record: {e}"
            print(f"Error inserting purchase transaction: {e}")

        #else:
        #    print(f"Please fill in all required fields")

        cur.execute('''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description,
                            FORMAT(ROUND(pt.purchase_price,2),2) AS price,
                            GROUP_CONCAT(DISTINCT c.color_name) color
                        FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, purchasetransactions pt, vehicles v
                                WHERE v.vehicle_typeID = vt.vehicle_typeID
                                 AND m.manufacturerID = v.manufacturerID
                                 AND v.vehicleID = vc.vehicleID
                                 AND vc.colorID = c.colorID
                                 AND pt.vehicleID = v.vehicleID
                                 AND v.vehicleID = %s
                               GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description''',
                    (vehicle_id,))
        vehicle = cur.fetchone()

        return render_template('transaction_complete.html', transaction_type='buy', vehicle=vehicle)

@app.route('/sell', methods=['GET', 'POST'])
def sell():

    # Connect to MariaDB Platform
    try:
        conn = db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    vehicle_id = None
    if "sellVehicleID" in request.form:
        vehicle_id = int(request.form['sellVehicleID'])
        session['sellVehicleID'] = vehicle_id
        customer_id = None

    # Execute Query
    cur.execute('''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description,
                        (CASE nvl(pt.purchase_price, 0)
                         WHEN 0 THEN '' 
                         ELSE FORMAT(ROUND((pt.purchase_price * 1.4) + nvl(p.parts_cost, 0), 2), 2)
                         END
                        ) AS sales_price,   
                        GROUP_CONCAT(DISTINCT c.color_name) color
                        FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, vehicles v
                            LEFT JOIN purchasetransactions pt ON v.vehicleID = pt.vehicleID
                            LEFT JOIN partorders po ON v.vehicleID = po.vehicleID
                            LEFT JOIN (SELECT part_orderID, (SUM(cost * quantity) * 1.2 ) AS parts_cost 
                                        FROM parts 
                                        GROUP BY part_orderID) p 
                                ON po.part_orderID = p.part_orderID
                                WHERE v.vehicle_typeID = vt.vehicle_typeID
                                 AND m.manufacturerID = v.manufacturerID
                                 AND v.vehicleID = vc.vehicleID
                                 AND vc.colorID = c.colorID
                                 AND v.vehicleID = %s
                               GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description''',
                (vehicle_id,))
    vehicle = cur.fetchone()

    # Execute Query
    cur.execute('''SELECT c.customerID, c.first_name, c.last_name
                        FROM customers c
                        ORDER BY c.last_name ASC, c.first_name ASC''')
    customers = cur.fetchall()

    return render_template('sell.html', vehicle=vehicle, customers=customers, customer_id=customer_id)


@app.route('/process_sale', methods=['GET', 'POST'])
def process_sale():
    # Connect to MariaDB Platform
    try:
        conn = db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        customer_id = request.form['customer']
        user_id = session['userID']
        sale_date = request.form['sale_date']

        vehicle_id = session['sellVehicleID']

        # Check that all required fields are not null
        #if customer_id and salesperson_id and purchase_date and purchase_price and vehicle_condition and vehicle_id:
        # Insert customer data into database
        try:
            cur.execute('''INSERT INTO salestransactions VALUES (
                            0, %s, %s, %s, %s
                            )''',
                        (vehicle_id, user_id, customer_id, sale_date))
            conn.commit()

        except mariadb.Error as e:
            # msg = "Error inserting customer record: {e}"
            print(f"Error inserting sale transaction: {e}")

        #else:
        #    print(f"Please fill in all required fields")

        cur.execute('''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description,
                            FORMAT(ROUND(pt.purchase_price,2),2) AS price,
                            GROUP_CONCAT(DISTINCT c.color_name) color
                        FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, purchasetransactions pt, vehicles v
                                WHERE v.vehicle_typeID = vt.vehicle_typeID
                                 AND m.manufacturerID = v.manufacturerID
                                 AND v.vehicleID = vc.vehicleID
                                 AND vc.colorID = c.colorID
                                 AND pt.vehicleID = v.vehicleID
                                 AND v.vehicleID = %s
                               GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description''',
                    (vehicle_id,))
        vehicle = cur.fetchone()

        return render_template('transaction_complete.html', transaction_type='sell', vehicle=vehicle)


@app.route("/login", methods=["POST", "GET"])
def login():
    # Connect to MariaDB Platform
    try:
        conn = db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        login_error = None

        result = cur.execute('''SELECT * FROM users WHERE username = %s ''', [username])

        # Check if match found for username
        if cur.rowcount > 0:
            data = cur.fetchone()

            # Check entered password against password stored in database for this user
            if password == data['password']:
                session['logged_in'] = True
                session['userID'] = data['userID']
                session['username'] = username
                session['first_name'] = data['first_name']
                session['role'] = data['role']
            else:
                login_error = 'Invalid Username or Password'
        else:
            login_error = 'Username Not Found'

        return render_template('base.html', login_error=login_error)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect('/')


'''
Easy launch of application

    If this ile is being executed, __name__ will be equal to __main__ and the code below it will run.

    More info can be found here: https://medium.com/@mycodingmantras/what-does-if-name-main-mean-in-python-fa6b0460a62d
    Scripts vs modules
'''
if __name__ == "__main__":
    app.run(debug=True)