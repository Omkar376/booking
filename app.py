from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
import yaml
import random
import pandas as pd
import requests
#import mapbox
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)

# Configure db
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
mysql = MySQL(app)


#MAPBOX_API_TOKEN = db['mapbox_api_token']
MAPBOX_API_TOKEN = 'pk.eyJ1IjoiYW5hbHl0aWNzbG4iLCJhIjoiY2pyMXZkYmMyMHl6eDQzcGN0cGl1cDZjbyJ9.J2MLiev145UG6Jnp3HT2Vg'
origin_list = {}
origin_list = []
destination_list = []
origin_list.append({'lat' : 19.076,'lon' :72.8777})
destination_list.append({'lat' : 22.7196
,'lon' :75.8577
})
destination_list.append({'lat' :18.5204
,'lon' :73.8567

})
destination_list.append({'lat' :28.367

,'lon' :79.4304

})
def get_estimated_time(origin_list, destination_list):
    #service = mapbox.DirectionsMatrix(access_token=MAPBOX_API_TOKEN)
    '''
    origin_features_list = encode_coordinates(origin_list)
    destination_features_list = encode_coordinates(destination_list)    
    list_of_features = origin_features_list + destination_features_list
    response = service.matrix(coordinates=list_of_features,
                                          profile='mapbox/driving',
                                          annotations=['du'],
                                          sources=[0],
                                          destinations=list(range(1,
                                                                  len(destination_list)+1)))
    '''
    lat_lon_string = ""
    for item in origin_list:
        lat_lon_string = lat_lon_string + str(item['lon']) + "," + str(item['lat']) +";"
    for item in destination_list:
        lat_lon_string = lat_lon_string + str(item['lon']) + "," + str(item['lat']) +";"
    destination_string = ';'.join(map(str, list(range(1,len(destination_list)+1))))
    query_string =  lat_lon_string[:-1] + f"?sources=0&destinations={destination_string}"   
    query_string = query_string + f"&access_token={MAPBOX_API_TOKEN}"
    url = "https://api.mapbox.com/directions-matrix/v1/mapbox/driving/"+ query_string
    response = requests.get(url)
    response_data = response.json()
    estimated_time_list = response_data['durations'][0]
    min_index = estimated_time_list.index(min(estimated_time_list))
    return min_index

def encode_coordinates(data):
    """Form string of lat lon co-ordinates to pass as param in clustering. """
    list_of_features = []
    for d in data:
        d['lat_lon'] = (d['lon'], d['lat'])
        temp =  {'geometry': {
       'type': 'Point',
       'coordinates': [d['lon'], d['lat']]}}
        list_of_features.append(temp)
    #list_of_features = [d['lat_lon'] for d in data]    
    return list_of_features


def assign_driver(cur, customer_latitude, customer_longitude):
    cur.execute("SELECT  * FROM drivers WHERE driver_status = 'Available';")
    driver_data = cur.fetchall()
    driver_df =  pd.DataFrame(driver_data, columns=['driver_name', 'latitude','longitude',	'address','driver_status'])
    driver_list = driver_df.to_dict('records')
    
    origin_list = []
    origin_list.append({'lat' : customer_latitude,'lon' :customer_longitude})
    destination_list = []
    for item in driver_list:
        destination_list.append({'lat' : item['latitude'],'lon' :item['longitude']})
    min_index = get_estimated_time(origin_list, destination_list)
    assigned_driver_name = driver_list[min_index]['driver_name']
    return assigned_driver_name

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for mile
    return c * r

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
        driver_name = assign_driver(cur, customer_latitude, customer_longitude)
        #driver_name = "test"       
        cur.execute("INSERT INTO orders(order_id, customer_name, latitude, longitude, address, driver_name) VALUES(%s, %s , %s , %s , %s , %s)"
                    ,(order_id, customer_name, customer_latitude, customer_longitude, customer_address, driver_name))
        cur.execute("UPDATE drivers SET driver_status = 'Busy' WHERE driver_name = '%s'"% (driver_name))
        mysql.connection.commit()
        cur.close()
        return redirect('/driver_status')
    return render_template('index.html')

@app.route('/driver_status')
def driver_status():
    cur = mysql.connection.cursor()
    cur.execute("SELECT customer_name, driver_name, FROM orders")    
    orders_tuple = cur.fetchall()
    order_df = pd.DataFrame(orders_tuple, columns=['customer_name','driver_name'])
    cur.execute("SELECT driver_name, driver_status  FROM drivers;")
    driver_tuple = cur.fetchall()
    driver_df =  pd.DataFrame(driver_tuple, columns=['driver_name', 'driver_status'])
    driver_df = driver_df.merge(order_df, left_on='driver_name', right_on='driver_name')
    mysql.connection.commit()
    cur.close()    
    return render_template('driver_status.html',orderDetails = driver_df)

if __name__ == '__main__':
    app.run(debug=True,port=8766)
