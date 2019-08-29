from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
import yaml
import random

app = Flask(__name__)

# Configure db
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)
def get_driver(cur, customer_latitude, customer_longitude):
    cur.execute("SELECT  * FROM drivers;")
    driver_data = cur.fetchall()
    return driver_data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Fetch form data
        orderDetails = request.form
        order_id = "O"+str(random.randint(10001,99999))
        customer_name = orderDetails['customer_name']
        customer_latitude = orderDetails['customer_latitude']
        customer_longitude = orderDetails['customer_longitude']
        customer_address = orderDetails['customer_address']
        cur = mysql.connection.cursor()
        #driver_name = get_driver(cur, customer_latitude, customer_longitude)
        driver_name = "test"       
        cur.execute("INSERT INTO orders(order_id, customer_name, latitude, longitude, address, driver_name) VALUES(%s, %s , %s , %s , %s , %s)"
                    ,(order_id, customer_name, customer_latitude, customer_longitude, customer_address, driver_name))
        cur.execute("UPDATE drivers "
                    ,(order_id, customer_name, customer_latitude, customer_longitude, customer_address, driver_name))
        mysql.connection.commit()
        cur.close()
        return redirect('/driver_status')
    return render_template('index.html')

@app.route('/driver_status')
def driver_status():
    cur = mysql.connection.cursor()
    orders = cur.execute("SELECT * FROM orders")    
    if orders > 0:
        orderDetails = cur.fetchall()
    cur.execute("SELECT  * FROM drivers;")
    driver_data = cur.fetchall()    
    mysql.connection.commit()
    cur.close()    
    return render_template('driver_status.html',orderDetails=orderDetails)

if __name__ == '__main__':
    app.run(debug=True,port=8766)
