import pandas as pd


def main():
    # Read only columns A to S of the "July" sheet (column T has image formulas)
    df = pd.read_excel("OLA_DataSet.xlsx", sheet_name="July", usecols="A:S")

    print("Shape:", df.shape)
    print("\nColumn types:")
    print(df.dtypes)

    print("\nMissing values per column:")
    print(df.isna().sum())

    print("\nBooking status counts:")
    print(df["Booking_Status"].value_counts())

    print("\nDuplicate Booking_IDs:", df["Booking_ID"].duplicated().sum())

    # Save a quick CSV so the next steps load faster than Excel
    df.to_csv("ola_raw.csv", index=False)
    print("\nSaved ola_raw.csv")


if __name__ == "__main__":
    main()