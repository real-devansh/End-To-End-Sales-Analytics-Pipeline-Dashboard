"""Generate analytics reports from processed CSV data."""
import pandas as pd
import os

df = pd.read_csv('data/processed/processed_data.csv')
out = 'data/processed'
os.makedirs(os.path.join(out, 'csv_reports'), exist_ok=True)

# 1. Total Revenue Summary
summary = pd.DataFrame([{
    'total_orders': len(df),
    'total_revenue': round(df['sales'].sum(), 2),
    'avg_order_value': round(df['sales'].mean(), 2),
    'min_sale': round(df['sales'].min(), 2),
    'max_sale': round(df['sales'].max(), 2),
}])
summary.to_csv(f'{out}/csv_reports/total_revenue_summary.csv', index=False)

# 2. Monthly Trend
monthly = df.groupby(['order_year', 'order_month', 'order_month_name']).agg(
    order_count=('sales', 'count'), total_revenue=('sales', 'sum'), avg_order=('sales', 'mean')
).reset_index().sort_values(['order_year', 'order_month'])
monthly.to_csv(f'{out}/csv_reports/monthly_revenue_trend.csv', index=False)

# 3. Category Performance
cat = df.groupby('category').agg(
    order_count=('sales', 'count'), total_revenue=('sales', 'sum'), avg_order=('sales', 'mean')
).reset_index().sort_values('total_revenue', ascending=False)
cat['revenue_share_pct'] = round(cat['total_revenue'] / cat['total_revenue'].sum() * 100, 2)
cat.to_csv(f'{out}/csv_reports/category_performance.csv', index=False)

# 4. Sub-Category
sub = df.groupby(['category', 'sub_category']).agg(
    order_count=('sales', 'count'), total_revenue=('sales', 'sum')
).reset_index().sort_values('total_revenue', ascending=False)
sub.to_csv(f'{out}/csv_reports/subcategory_performance.csv', index=False)

# 5. Top 10 Customers
cust = df.groupby(['customer_id', 'customer_name', 'segment']).agg(
    total_orders=('sales', 'count'), total_revenue=('sales', 'sum')
).reset_index().sort_values('total_revenue', ascending=False).head(10)
cust.to_csv(f'{out}/csv_reports/top_10_customers.csv', index=False)

# 6. Region Performance
reg = df.groupby('region').agg(
    states=('state', 'nunique'), cities=('city', 'nunique'),
    total_orders=('sales', 'count'), total_revenue=('sales', 'sum')
).reset_index().sort_values('total_revenue', ascending=False)
reg.to_csv(f'{out}/csv_reports/region_performance.csv', index=False)

# 7. Top 10 States
states = df.groupby(['state', 'region']).agg(
    total_orders=('sales', 'count'), total_revenue=('sales', 'sum')
).reset_index().sort_values('total_revenue', ascending=False).head(10)
states.to_csv(f'{out}/csv_reports/top_10_states.csv', index=False)

# 8. Shipping Mode
ship = df.groupby('ship_mode').agg(
    total_orders=('sales', 'count'), total_revenue=('sales', 'sum'),
    avg_shipping_days=('shipping_days', 'mean')
).reset_index().sort_values('total_revenue', ascending=False)
ship.to_csv(f'{out}/csv_reports/shipping_mode_analysis.csv', index=False)

# 9. Yearly Revenue
yr = df.groupby('order_year').agg(
    total_orders=('sales', 'count'), total_revenue=('sales', 'sum')
).reset_index().sort_values('order_year')
yr.to_csv(f'{out}/csv_reports/yearly_revenue.csv', index=False)

# 10. Segment Analysis
seg = df.groupby('segment').agg(
    unique_customers=('customer_id', 'nunique'), total_orders=('sales', 'count'),
    total_revenue=('sales', 'sum')
).reset_index().sort_values('total_revenue', ascending=False)
seg.to_csv(f'{out}/csv_reports/segment_analysis.csv', index=False)

# 11. Top 10 Products
prod = df.groupby(['product_name', 'category', 'sub_category']).agg(
    times_ordered=('sales', 'count'), total_revenue=('sales', 'sum')
).reset_index().sort_values('total_revenue', ascending=False).head(10)
prod.to_csv(f'{out}/csv_reports/top_10_products.csv', index=False)

# 12. Top 10 Cities
cities = df.groupby(['city', 'state', 'region']).agg(
    total_orders=('sales', 'count'), total_revenue=('sales', 'sum')
).reset_index().sort_values('total_revenue', ascending=False).head(10)
cities.to_csv(f'{out}/csv_reports/top_10_cities.csv', index=False)

# 13. Quarterly Revenue
qtr = df.groupby(['order_year', 'order_quarter']).agg(
    order_count=('sales', 'count'), total_revenue=('sales', 'sum')
).reset_index().sort_values(['order_year', 'order_quarter'])
qtr.to_csv(f'{out}/csv_reports/quarterly_revenue.csv', index=False)

# 14. Sales Tier Distribution
tier = df.groupby('sales_tier').agg(
    order_count=('sales', 'count'), total_revenue=('sales', 'sum'),
    avg_sale=('sales', 'mean'), min_sale=('sales', 'min'), max_sale=('sales', 'max')
).reset_index()
tier.to_csv(f'{out}/csv_reports/sales_tier_distribution.csv', index=False)

# 15. Day of Week Analysis
dow = df.groupby('order_day_of_week').agg(
    total_orders=('sales', 'count'), total_revenue=('sales', 'sum')
).reset_index().sort_values('total_revenue', ascending=False)
dow.to_csv(f'{out}/csv_reports/day_of_week_analysis.csv', index=False)

# Write master Excel report
with pd.ExcelWriter(f'{out}/analytics_report.xlsx', engine='openpyxl') as w:
    summary.to_excel(w, sheet_name='Revenue Summary', index=False)
    monthly.to_excel(w, sheet_name='Monthly Trend', index=False)
    cat.to_excel(w, sheet_name='Category Performance', index=False)
    sub.to_excel(w, sheet_name='SubCategory Performance', index=False)
    cust.to_excel(w, sheet_name='Top 10 Customers', index=False)
    reg.to_excel(w, sheet_name='Region Performance', index=False)
    states.to_excel(w, sheet_name='Top 10 States', index=False)
    cities.to_excel(w, sheet_name='Top 10 Cities', index=False)
    ship.to_excel(w, sheet_name='Shipping Mode', index=False)
    yr.to_excel(w, sheet_name='Yearly Revenue', index=False)
    qtr.to_excel(w, sheet_name='Quarterly Revenue', index=False)
    seg.to_excel(w, sheet_name='Segment Analysis', index=False)
    prod.to_excel(w, sheet_name='Top 10 Products', index=False)
    tier.to_excel(w, sheet_name='Sales Tier', index=False)
    dow.to_excel(w, sheet_name='Day of Week', index=False)

print('DONE - Reports generated:')
for f in sorted(os.listdir(f'{out}/csv_reports')):
    print(f'  - {f}')
print(f'  - analytics_report.xlsx (15 sheets)')
print()
r = summary.iloc[0]
print(f"Total Revenue: ${r['total_revenue']:,.2f}")
print(f"Total Orders : {int(r['total_orders']):,}")
print(f"Avg Order    : ${r['avg_order_value']:,.2f}")
print(f"Max Sale     : ${r['max_sale']:,.2f}")
