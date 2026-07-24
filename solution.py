import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for reproducible inline charts
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

def generate_raw_playstore_dataset():
    """
    Generates a realistic Google Play Store dataset matching Kaggle schema
    with intentional missing values, bad types, duplicate rows, and outliers.
    """
    os.makedirs("data", exist_ok=True)
    np.random.seed(42)
    
    categories = ['GAME', 'FAMILY', 'TOOLS', 'BUSINESS', 'PRODUCTIVITY', 'FINANCE', 'MEDICAL']
    content_ratings = ['Everyone', 'Teen', 'Everyone 10+', 'Mature 17+']
    
    data = []
    for i in range(1, 501):
        app_name = f"App_{i}"
        category = np.random.choice(categories)
        
        # Introduce missing rating (~12%)
        rating = np.nan if np.random.rand() < 0.12 else round(np.random.uniform(1.0, 5.0), 1)
        
        reviews = str(np.random.randint(10, 500000))
        
        # Uncleaned size (e.g. '19M', '1000k', 'Varies with device')
        if np.random.rand() < 0.1:
            size = "Varies with device"
        else:
            size = f"{np.random.randint(1, 100)}M"
            
        installs = f"{np.random.choice([1000, 50000, 100000, 1000000, 5000000]):,}+"
        app_type = "Free" if np.random.rand() > 0.15 else "Paid"
        price = "$0" if app_type == "Free" else f"${round(np.random.uniform(0.99, 19.99), 2)}"
        content_rating = np.random.choice(content_ratings)
        
        # Introduce missing current ver
        current_ver = None if np.random.rand() < 0.05 else f"{np.random.randint(1,5)}.{np.random.randint(0,9)}"
        
        data.append([app_name, category, rating, reviews, size, installs, app_type, price, content_rating, current_ver])
    
    df = pd.DataFrame(data, columns=[
        'App', 'Category', 'Rating', 'Reviews', 'Size', 'Installs', 
        'Type', 'Price', 'Content Rating', 'Current Ver'
    ])
    
    # Inject deliberate duplicate rows for cleaning task
    df = pd.concat([df, df.iloc[:15]], ignore_index=True)
    
    # Inject numeric outliers into Reviews
    df.loc[10, 'Reviews'] = "15000000"
    df.loc[25, 'Reviews'] = "22000000"
    
    df.to_csv("data/googleplaystore_raw.csv", index=False)
    print("[Data Generation] Raw dataset saved to data/googleplaystore_raw.csv")
    return df

def run_data_engineering_pipeline():
    # Step 1: Load and Display Diagnostic Info
    df_raw = generate_raw_playstore_dataset()
    print("\n--- 1. RAW DATASET METRICS ---")
    print(f"Dataset Shape: {df_raw.shape}")
    print("\nDataFrame Info:")
    df_raw.info()
    print("\nDataFrame Summary Statistics:")
    print(df_raw.describe(include='all'))
    
    # Step 2: Data Cleaning
    df = df_raw.copy()
    
    # A. Deduplication
    df = df.drop_duplicates()
    
    # B. Type Conversion & String Cleansing
    df['Reviews'] = pd.to_numeric(df['Reviews'], errors='coerce')
    
    # Clean Price
    df['Price'] = df['Price'].astype(str).str.replace('$', '', regex=False).str.strip()
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0.0)
    
    # Clean Installs
    df['Installs'] = df['Installs'].astype(str).str.replace('+', '', regex=False).str.replace(',', '', regex=False)
    df['Installs'] = pd.to_numeric(df['Installs'], errors='coerce')
    
    # C. Missing Value Handling
    # Rating has ~12% missing (<10% limit rule evaluation -> drop rows or median impute depending on exact threshold)
    # Strategy: Impute numeric Rating with Median; Impute Current Ver with Mode
    rating_median = df['Rating'].median()
    df['Rating'] = df['Rating'].fillna(rating_median)
    
    ver_mode = df['Current Ver'].mode()[0]
    df['Current Ver'] = df['Current Ver'].fillna(ver_mode)
    
    # D. Outlier Detection & Capping using IQR on 'Reviews' and 'Installs'
    for col in ['Reviews', 'Installs']:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        # Cap upper outliers to 95th percentile
        cap_value = df[col].quantile(0.95)
        df[col] = np.where(df[col] > upper_bound, cap_value, df[col])
        df[col] = np.where(df[col] < lower_bound, lower_bound, df[col])

    df.to_csv("data/googleplaystore_cleaned.csv", index=False)
    print(f"\n[Clean Success] Dataset cleaned. Final shape: {df.shape}")

    # Step 3: Local SQLite Database Setup & Execution
    conn = sqlite3.connect("playstore.db")
    df.to_sql("apps", conn, if_exists="replace", index=False)
    
    queries = [
        ("Query 1: WHERE Filter (Price > $0)", 
         "SELECT App, Category, Price, Rating FROM apps WHERE Price > 0 AND Rating >= 4.0 LIMIT 5;"),
        
        ("Query 2: GROUP BY + Aggregation (AVG Rating by Category)", 
         "SELECT Category, COUNT(*) as Total_Apps, ROUND(AVG(Rating), 2) as Avg_Rating FROM apps GROUP BY Category;"),
        
        ("Query 3: HAVING Clause Filter", 
         "SELECT Category, COUNT(*) as App_Count, ROUND(AVG(Installs), 0) as Avg_Installs FROM apps GROUP BY Category HAVING COUNT(*) > 40;"),
        
        ("Query 4: ORDER BY + LIMIT Top 5 Installed Apps", 
         "SELECT App, Category, Installs, Reviews FROM apps ORDER BY Installs DESC, Reviews DESC LIMIT 5;"),
        
        ("Query 5: Combined WHERE Conditions (AND/OR)", 
         "SELECT App, Category, Type, Rating, Price FROM apps WHERE (Type = 'Paid' AND Price < 5.0) OR (Rating >= 4.8 AND Installs > 100000);"),
        
        ("Query 6: High Review-to-Install Ratio Analysis", 
         "SELECT App, Category, Reviews, Installs, ROUND((Reviews * 1.0 / Installs), 4) as Engagement_Ratio FROM apps WHERE Installs > 10000 ORDER BY Engagement_Ratio DESC LIMIT 5;")
    ]
    
    print("\n--- 3. SQL QUERY EXECUTIONS ---")
    with open("queries.sql", "w") as f:
        for title, q in queries:
            print(f"\n>>> {title}\nSQL: {q}")
            f.write(f"-- {title}\n{q}\n\n")
            res = pd.read_sql_query(q, conn)
            print(res.to_string(index=False))
            
    conn.close()

    # Step 4: Generate 5 Visualizations
    # Chart 1: Box Plot (Outlier Check)
    plt.figure()
    sns.boxplot(x=df['Rating'], color='skyblue')
    plt.title('Chart 1: App Rating Distribution & Outlier Check')
    plt.xlabel('App Rating (1.0 - 5.0)')
    plt.tight_layout()
    plt.savefig('chart1_boxplot.png')
    plt.close()

    # Chart 2: Histogram
    plt.figure()
    sns.histplot(df['Reviews'], bins=20, kde=True, color='purple')
    plt.title('Chart 2: Log-Scaled Distribution of User Reviews')
    plt.xlabel('Capped Review Count')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig('chart2_histogram.png')
    plt.close()

    # Chart 3: Bar Chart from value_counts()
    plt.figure()
    df['Category'].value_counts().plot(kind='bar', color='teal')
    plt.title('Chart 3: Total App Count by Category')
    plt.xlabel('Category Name')
    plt.ylabel('Total Apps')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('chart3_barchart.png')
    plt.close()

    # Chart 4: Scatter Plot
    plt.figure()
    sns.scatterplot(data=df, x='Reviews', y='Installs', hue='Type', alpha=0.7)
    plt.title('Chart 4: User Reviews vs. Total Installs by App Type')
    plt.xlabel('Total Reviews')
    plt.ylabel('Total Installs')
    plt.tight_layout()
    plt.savefig('chart4_scatterplot.png')
    plt.close()

    # Chart 5: Aggregated GroupBy Bar Chart
    plt.figure()
    df.groupby('Category')['Price'].mean().sort_values(ascending=False).plot(kind='bar', color='coral')
    plt.title('Chart 5: Average App Price ($) by Category')
    plt.xlabel('App Category')
    plt.ylabel('Mean Price ($)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('chart5_groupby_chart.png')
    plt.close()
    
    print("\n[Visualizations Complete] 5 charts saved and generated successfully.")

if __name__ == "__main__":
    run_data_engineering_pipeline()
