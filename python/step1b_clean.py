import pandas as pd


def main():
    df = pd.read_csv("ola_raw.csv", parse_dates=["Date"])

    # 1. Remove extra spaces from all text columns
    text_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in text_cols:
        df[col] = df[col].str.strip()

    # 2. Blank text columns mean "not applicable", so label them clearly
    na_cols = [
        "Canceled_Rides_by_Customer",
        "Canceled_Rides_by_Driver",
        "Incomplete_Rides",
        "Incomplete_Rides_Reason",
        "Payment_Method",
    ]
    df[na_cols] = df[na_cols].fillna("Not Applicable")

    # 3. Numeric blanks (TAT, ratings) stay empty so averages stay correct

    # 4. Create new columns for analysis
    df["Hour"] = df["Date"].dt.hour
    df["Day_Name"] = df["Date"].dt.day_name()
    df["Booking_Date"] = df["Date"].dt.date
    df["Time_Slot"] = pd.cut(
        df["Hour"],
        bins=[-1, 5, 11, 16, 20, 23],
        labels=["Late Night", "Morning", "Afternoon", "Evening", "Night"],
    )
    # Revenue counts only completed rides
    df["Revenue"] = df["Booking_Value"].where(df["Booking_Status"] == "Success", 0)

    # 5. Quick checks
    print("Rating range:", df["Driver_Ratings"].min(), "to", df["Driver_Ratings"].max())
    print("Rows with Booking_Value <= 0:", (df["Booking_Value"] <= 0).sum())
    print("Total revenue (success only):", df["Revenue"].sum())
    print("\nTime slots:\n", df["Time_Slot"].value_counts())
    print("\nPayment methods:\n", df["Payment_Method"].value_counts())

    df.to_csv("ola_clean.csv", index=False)
    print("\nSaved ola_clean.csv with shape", df.shape)


if __name__ == "__main__":
    main()