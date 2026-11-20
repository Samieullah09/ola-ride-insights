USE ola_db;

-- Q1. All successful bookings
SELECT * FROM bookings WHERE Booking_Status = 'Success';

-- Q2. Average ride distance for each vehicle type (completed rides only)
SELECT Vehicle_Type, ROUND(AVG(Ride_Distance), 2) AS Avg_Distance_Km
FROM bookings
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type;

-- Q3. Total rides cancelled by customers
SELECT COUNT(*) AS Cancelled_By_Customers
FROM bookings
WHERE Booking_Status = 'Canceled by Customer';

-- Q4. Top 5 customers with the most rides
SELECT Customer_ID, COUNT(*) AS Total_Rides
FROM bookings
GROUP BY Customer_ID
ORDER BY Total_Rides DESC, Customer_ID
LIMIT 5;

-- Q5. Rides cancelled by drivers for personal and car related issues
SELECT COUNT(*) AS Driver_Cancel_Personal_Car
FROM bookings
WHERE Canceled_Rides_by_Driver = 'Personal & Car related issue';

-- Q6. Max and min driver rating for Prime Sedan
SELECT MAX(Driver_Ratings) AS Max_Rating, MIN(Driver_Ratings) AS Min_Rating
FROM bookings
WHERE Vehicle_Type = 'Prime Sedan';

-- Q7. Rides paid using UPI
SELECT * FROM bookings WHERE Payment_Method = 'UPI';

-- Q8. Average customer rating per vehicle type
SELECT Vehicle_Type, ROUND(AVG(Customer_Rating), 2) AS Avg_Customer_Rating
FROM bookings
GROUP BY Vehicle_Type;

-- Q9. Total booking value of successful rides
SELECT SUM(Booking_Value) AS Total_Booking_Value
FROM bookings
WHERE Booking_Status = 'Success';

-- Q10. All incomplete rides with the reason
SELECT Booking_ID, Vehicle_Type, Incomplete_Rides_Reason
FROM bookings
WHERE Incomplete_Rides = 'Yes';