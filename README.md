# Ola Ride Insights

End-to-end analysis of **103,024 Ola ride bookings (July 2024, Bengaluru)**: data cleaning in Python, 10 SQL queries in MySQL, a 5-page Power BI dashboard and a Streamlit web app.

**Live app:** *https://ola-rides-insight.streamlit.app/*

What this project answers

Which vehicles earn the most, when demand peaks, why rides get cancelled and how drivers and customers rate each other.

## Tools

Python (Pandas), MySQL, Power BI (DAX), Streamlit, Plotly

## Project steps

1. **Data cleaning** (`python/step1b\_clean.py`): trimmed text, filled blanks in text columns with "Not Applicable", kept ratings and turnaround times as empty values, added Hour, Day\_Name, Time\_Slot and Revenue columns. No duplicate booking IDs were found.
2. **SQL** (`sql/ola\_queries.sql`): the 10 questions from the brief on the `bookings` table.
3. **Power BI** (`powerbi/dashboard.pbix`): 5 pages (Overall, Vehicle Type, Revenue, Cancellation, Ratings) with a vehicle slicer synced across pages.
4. **Streamlit app** (`app.py`): sidebar filters, KPI cards, 8 tabs, an SQL Lab with a read-only playground, and the Power BI pages.
5. **Insights report** (`Ola\_Ride\_Insights\_Report.pdf`): 15 pages with findings, recommendations, SQL answers and limitations.

## Dashboard

!\[Overall](dashboard/1\_overall.png)
!\[Vehicle Type](dashboard/2\_vehicle\_type.png)
!\[Revenue](dashboard/3\_revenue.png)
!\[Cancellation](dashboard/4\_cancellation.png)
!\[Ratings](dashboard/5\_ratings.png)

> Power BI "Publish to web" needs a work/school account, so the Streamlit app shows dashboard screenshots. The interactive report is in `powerbi/dashboard.pbix`.

## Key insights

* 62.1% of bookings were completed. Customers cancelled 10.2%, drivers 17.9% and 9.8% found no driver. Drivers cancel about 1.8 times as often as customers.
* Completed rides earned about ₹3.51 Cr (average ₹548 per ride). Cash (55%) and UPI (40%) make up almost all payments.
* Demand is steady: about 3,300 bookings per day and 4,176 to 4,408 per hour, so there is no clear rush hour.
* Auto trips are short (about 10 km) while every other vehicle averages about 25 km. Fare has almost no link with distance (correlation 0.002), so Auto earns about ₹55 per km against about ₹22 for the rest.
* The top driver cancellation reason is "Personal \& Car related issue" (6,542). The top customer reason is "Driver is not moving towards pickup location" (3,175).
* Only 8% of customers booked more than once in the month.
* Ratings are spread evenly between 3.0 and 5.0 and average 4.00 for both drivers and customers.

## Limitations

The data covers one month (July 2024) and Bengaluru only, so it cannot show seasonality, month-to-month trends or other cities. Ratings, hourly demand and fares look very evenly spread, which suggests the dataset may be synthetic.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Folder structure

```
app.py                          Streamlit app
queries.py                      the 10 SQL queries used by the app
ola\_clean.csv                   cleaned dataset
Ola\_Ride\_Insights\_Report.pdf    insights report
requirements.txt
assets/                         logo and vehicle icons
dashboard/                      Power BI page screenshots
powerbi/dashboard.pbix          interactive Power BI report
python/                         cleaning and MySQL loading scripts
sql/ola\_queries.sql             the 10 SQL queries
.streamlit/config.toml          app theme
```

**Author:** Samieullah Khan

