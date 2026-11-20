import fitz  # PyMuPDF

# Page order in Power BI must match this list
names = ["1_overall", "2_vehicle_type", "3_revenue", "4_cancellation", "5_ratings"]

doc = fitz.open("Ola_Ride_Insights.pdf")
for page, name in zip(doc, names):
    page.get_pixmap(dpi=150).save(f"dashboard/{name}.png")
    print("saved", name)