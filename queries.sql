-- Query 1: WHERE Filter (Price > $0)
SELECT App, Category, Price, Rating FROM apps WHERE Price > 0 AND Rating >= 4.0 LIMIT 5;

-- Query 2: GROUP BY + Aggregation (AVG Rating by Category)
SELECT Category, COUNT(*) as Total_Apps, ROUND(AVG(Rating), 2) as Avg_Rating FROM apps GROUP BY Category;

-- Query 3: HAVING Clause Filter
SELECT Category, COUNT(*) as App_Count, ROUND(AVG(Installs), 0) as Avg_Installs FROM apps GROUP BY Category HAVING COUNT(*) > 40;

-- Query 4: ORDER BY + LIMIT Top 5 Installed Apps
SELECT App, Category, Installs, Reviews FROM apps ORDER BY Installs DESC, Reviews DESC LIMIT 5;

-- Query 5: Combined WHERE Conditions (AND/OR)
SELECT App, Category, Type, Rating, Price FROM apps WHERE (Type = 'Paid' AND Price < 5.0) OR (Rating >= 4.8 AND Installs > 100000);

-- Query 6: High Review-to-Install Ratio Analysis
SELECT App, Category, Reviews, Installs, ROUND((Reviews * 1.0 / Installs), 4) as Engagement_Ratio FROM apps WHERE Installs > 10000 ORDER BY Engagement_Ratio DESC LIMIT 5;
