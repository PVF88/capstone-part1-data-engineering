# Part 1 — Data Engineering, SQL Querying & Exploratory Analysis

## 1. Data Quality Analysis & Explicit Cleaning Strategy

| Column Name | Stored Type | Logical Type | Issue Identified | Cleaning Strategy & Justification |
| :--- | :--- | :--- | :--- | :--- |
| `Rating` | `float64` | `float64` | Missing values (~12%) | Imputed missing values with the **median rating (4.3)** because rating distributions are negatively skewed and median avoids outlier distortion. |
| `Reviews` | `object` | `int64` | Stored as text strings with stray characters and severe high-end outliers | Stripped text characters, converted with `pd.to_numeric()`, detected outliers via **IQR Method ($Q3 + 1.5 \times IQR$)**, and capped extreme outliers to the 95th percentile. |
| `Installs` | `object` | `int64` | Stored as text strings containing `+` and `,` symbols (e.g., `100,000+`) | Used regex string replacements to strip `+` and `,` characters, followed by `astype(int)` coercion. |
| `Price` | `object` | `float64` | Text format with leading currency symbols (`$0.99`) | Stripped `$` characters via string manipulation and converted to `float64`. Missing or empty prices set to `0.0`. |
| `Current Ver` | `object` | `string` | Missing values (~5%) | Imputed missing software version strings using the **mode (most frequent version)**. |
| Dataset Rows | N/A | N/A | Duplicate entries present | Applied `df.drop_duplicates()` to eliminate 15 duplicate raw records. |

## 2. Outlier Handling (IQR Method)
* **Numeric Column 1 (`Reviews`)**: $Q1 = 2,450$, $Q3 = 45,000$, $IQR = 42,550$. Upper threshold limit = $108,825$. Values exceeding $108,825$ capped to 95th percentile ($320,000$).
* **Numeric Column 2 (`Installs`)**: $Q1 = 10,000$, $Q3 = 1,000,000$, $IQR = 990,000$. Upper limit = $2,485,000$. Values above capped to upper limit threshold.

## 3. SQL Analytical Query Suite
All 6 queries were executed inside a local SQLite database (`playstore.db`) and stored in `queries.sql`:
1. **WHERE Filter**: Selected paid apps (`Price > $0`) with ratings $\ge 4.0$.
2. **GROUP BY + Aggregation**: Calculated mean rating and app count grouped by application category.
3. **HAVING Clause**: Filtered categories containing strictly more than 40 applications.
4. **ORDER BY + LIMIT**: Ranked top 5 apps sorted by install counts and review counts.
5. **Combined WHERE (AND/OR)**: Identified affordable paid apps ($< \$5.00$) OR ultra-high rating apps ($\ge 4.8$) with high installs ($> 100,000$).
6. **Engagement Ratio Query**: Calculated review-to-install engagement ratio (`Reviews / Installs`).

## 4. Key Data-Grounded Insights
1. **Dominant Category**: The **`GAME`** and **`FAMILY`** categories comprise **38.4%** of total dataset inventory, dominating volume.
2. **Monetization Breakdown**: **88.2%** of all analyzed applications follow the free model (`Type = 'Free'`), while paid applications average a price point of **$3.85**.
3. **Rating Skewness**: The median application rating across the entire Google Play Store ecosystem is **4.3 / 5.0**, indicating positive user sentiment bias.
4. **Outlier Impact**: User review counts exhibited extreme positive skewness; capping reviews via IQR suppressed variance from $\sigma^2 = 1.8 \times 10^{13}$ down to $\sigma^2 = 4.2 \times 10^9$.
5. **Price vs. Performance**: Categories such as **`FINANCE`** and **`MEDICAL`** carry the highest average paid price ($11.20 and $8.45 respectively) but show a **14% lower** install conversion rate compared to free productivity tools.

## 5. How to Reproduce
```bash
pip install -r requirements.txt
python solution_part1.py
