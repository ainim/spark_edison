import mysql.connector
from datetime import datetime

DB_USER 	= "edison"
PASSWORD 	= "edison123"
DB_SERVER 	= "10.170.32.17"
DB_NAME 	= "edison"

class MySQLConnector(object):
    """ A connector to MySQL database """

    def __init__(self):
	self.alerts_insert		= ("INSERT INTO alerts "
						   "(date,node_id,status)"
						   "VALUES (%s,%s,%s)")
        self.meas_insert 		= ("INSERT INTO meas "
					   "(node_id, date, mea, type_mea) "  
					   "VALUES (%s, %s, %s, %s)")
	self.meas_type_insert 		= ("INSERT INTO meas_type "
				   	   "(id, type, unit)"
				   	   "VALUES (%s,%s,%s)")
	self.nodes_insert		= ("INSERT INTO nodes "
					   "(latitud, longitud)"
					   "VALUES (%s,%s)")
    def connect(self):
        try:
            self.cnx = mysql.connector.connect(user=DB_USER, 
                                               password=PASSWORD, 
                                               host=DB_SERVER, 
                                               database=DB_NAME)
        except mysql.connector.Error as err:
            print "Failed to connect"
            print err

    def disconnect(self):
        self.cnx.close()

    def insert_data(self, insert_stmt, values):
        cursor = self.cnx.cursor()
        try:
            cursor.execute(insert_stmt, values);
            self.cnx.commit()
        except Exception as e:
            print "Failed to insert data"
            print e
        cursor.close()

def insertAlert(datatime, node, status):
    conn = MySQLConnector()
    try:
        conn.connect()
    except Exception as e:
        print "Unable to connect to server"
        print e

	
    values = (datatime, node, status)
    conn.insert_data(conn.alerts_insert,values)	
    conn.disconnect()
