import psycopg2


def connect_to_database():
    try:
        pass
        connection = psycopg2.connect(
            host="localhost",
            port="5432",
            database="Bankdatabase",
            user="postgres",
            password ="Sh@rma2905",
        )
        print("Connected to postgreSQL database !")
        return connection
    except Exception as error:
        print("Error connection to PostgreSQL database:",error)
        return None

if __name__ =="__main__":
  conn =connect_to_database()
  if conn:
      conn.close()
      print("Conncetion closed.")

