import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Change these to match your MySQL setup
USER = "root"
PASSWORD = "your password"
HOST = "localhost"
PORT = 3306

CREATE_TABLE = """
CREATE TABLE bookings (
    Booking_DateTime           DATETIME,
    Booking_ID                 VARCHAR(20) PRIMARY KEY,
    Booking_Status             VARCHAR(30),
    Customer_ID                VARCHAR(20),
    Vehicle_Type               VARCHAR(20),
    Pickup_Location            VARCHAR(50),
    Drop_Location              VARCHAR(50),
    V_TAT                      INT NULL,
    C_TAT                      INT NULL,
    Canceled_Rides_by_Customer VARCHAR(60),
    Canceled_Rides_by_Driver   VARCHAR(60),
    Incomplete_Rides           VARCHAR(20),
    Incomplete_Rides_Reason    VARCHAR(30),
    Booking_Value              INT,
    Payment_Method             VARCHAR(20),
    Ride_Distance              INT,
    Driver_Ratings             DECIMAL(2,1) NULL,
    Customer_Rating            DECIMAL(2,1) NULL,
    Hour                       TINYINT,
    Day_Name                   VARCHAR(10),
    Booking_Date               DATE,
    Time_Slot                  VARCHAR(12),
    Revenue                    INT
)
"""


def make_engine(database=None):
    url = URL.create("mysql+pymysql", username=USER, password=PASSWORD,
                     host=HOST, port=PORT, database=database)
    return create_engine(url)


def main():
    # 1. Create the database
    with make_engine().begin() as conn:
        conn.execute(text("CREATE DATABASE IF NOT EXISTS ola_db"))

    # 2. Create a fresh bookings table
    engine = make_engine("ola_db")
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS bookings"))
        conn.execute(text(CREATE_TABLE))

    # 3. Load the clean CSV (drop the duplicate Time column, rename Date)
    df = pd.read_csv("ola_clean.csv", parse_dates=["Date"])
    df = df.drop(columns=["Time"]).rename(columns={"Date": "Booking_DateTime"})
    df.to_sql("bookings", engine, if_exists="append", index=False, chunksize=5000)

    # 4. Verify the load
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM bookings")).scalar()
        print("Rows loaded:", total)
        rows = conn.execute(text(
            "SELECT Booking_Status, COUNT(*) FROM bookings GROUP BY Booking_Status"))
        for status, count in rows:
            print(status, count)


if __name__ == "__main__":
    main()