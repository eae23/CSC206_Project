from flask import Flask, request, render_template
import mariadb
import myDatabase as db
import sys

# Launch app and define where the static assets will be located
app = Flask(__name__, static_url_path='/assets')

@app.route('/')
def base():

    return render_template('base.html')

@app.route('/vehicles')
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


@app.route('/vehicles_search')
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

    # Execute Query
    cur.execute( '''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name,
		FORMAT(ROUND((pt.purchase_price * 1.4) + nvl(p.parts_cost, 0),2),2) AS sales_price,
		GROUP_CONCAT(DISTINCT c.color_name) color
FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, purchasetransactions pt, vehicles v
	LEFT JOIN partorders po ON v.vehicleID = po.vehicleID
	LEFT JOIN (SELECT part_orderID, (SUM(cost) * 1.2 ) AS parts_cost 
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
    return render_template('vehicles/listing.html', vehicles=output, forsale=True)

@app.route('/details', methods=['GET', 'POST'])
def details():
    vehicle_id = int(request.form['vehicleID'])
    print(f"VehicleID: {vehicle_id}")

    # Connect to MariaDB Platform
    try:
        conn = db.myConnect()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor(dictionary=True)

    # Execute Query
    cur.execute('''SELECT v.vehicleID, v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description,
    		FORMAT(ROUND((pt.purchase_price * 1.4) + nvl(p.parts_cost, 0),2),2) AS sales_price,
		GROUP_CONCAT(DISTINCT c.color_name) color
    FROM vehicletypes vt, manufacturers m, vehiclecolors vc, colors c, purchasetransactions pt, vehicles v
    	LEFT JOIN partorders po ON v.vehicleID = po.vehicleID
    	LEFT JOIN (SELECT part_orderID, (SUM(cost) * 1.2 ) AS parts_cost 
    				FROM parts 
    				GROUP BY part_orderID) p 
    		ON po.part_orderID = p.part_orderID
            WHERE v.vehicle_typeID = vt.vehicle_typeID
             AND m.manufacturerID = v.manufacturerID
             AND v.vehicleID = vc.vehicleID
             AND vc.colorID = c.colorID
             AND pt.vehicleID = v.vehicleID
             AND v.vehicleID = %s
           GROUP BY v.vin, vt.vehicle_type_name, v.model_year, m.manufacturer_name, v.model_name, v.description''', (vehicle_id, ))
    output = cur.fetchall()

    return render_template('vehicles/details.html', vehicles=output)

@app.route('/sales_productivity')
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
                          ROUND((p.cost * 1.2), 2) SalesPrice
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


@app.route('/seller_history')
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


@app.route('/part_statistics')
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


@app.route('/buy')
def buy():
    return render_template('buy.html')


@app.route('/customers')
def customers():
    return render_template('customers.html')


@app.route('/parts')
def parts():
    return render_template('parts.html')


@app.route('/sell')
def sell():
    return render_template('sell.html')


@app.route('/suppliers')
def suppliers():
    return render_template('suppliers.html')


'''
Easy launch of application

    If this ile is being executed, __name__ will be equal to __main__ and the code below it will run.

    More info can be found here: https://medium.com/@mycodingmantras/what-does-if-name-main-mean-in-python-fa6b0460a62d
    Scripts vs modules
'''
if __name__ == "__main__":
    app.run(debug=True)