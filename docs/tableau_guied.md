# Tableau Dashboard Guide

This guide explains how to connect Tableau to the SQL Server database and create interactive dashboards for strategy analysis.

---

## Database Connection Setup

### Step 1: Connect Tableau to SQL Server

1. Open Tableau Desktop
2. Click **"Microsoft SQL Server"** under "Connect"
3. Enter connection details:
   - **Server**: `localhost` (or your server name)
   - **Database**: `StockCryptoDB`
   - **Authentication**: Windows Authentication (or SQL Server)
4. Click **"Sign In"**

### Step 2: Select Data Sources

Use the pre-built views for optimal performance:

**Primary Views:**
- `vw_strategy_comparison` - Aggregated performance metrics
- `vw_daily_strategy_performance` - Time-series data
- `vw_all_trades` - Individual trade records

**Raw Tables** (for custom calculations):
- `fact_prices` + `dim_ticker` + `dim_date`
- `fact_strategy_summary` + `dim_strategy`

---

## Dashboard 1: Strategy Performance Comparison

**Purpose**: Compare all strategies across all tickers at a glance.

### Data Source
Connect to `vw_strategy_comparison`

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  FILTERS: [Asset Type ▼] [Ticker ▼] [Strategy ▼]      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊 Total Return % (Bar Chart)                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│   Buy and Hold      ████████████ 22.1%                  │
│   SMA Crossover     ████████████████ 28.7%              │
│   Bollinger Bands   ████████████████████ 34.2%          │
│   ...                                                    │
│                                                          │
├──────────────────────┬──────────────────────────────────┤
│                      │                                   │
│  🎯 Risk/Return      │  📋 Performance Table            │
│     Scatter Plot     │                                   │
│                      │  Strategy  | Return | Sharpe     │
│  Sharpe Ratio (Y)    │  ─────────────────────────────   │
│         ↑            │  Bollinger | 34.2%  | 1.42       │
│       1.5│  ● ●      │  SMA Cross | 28.7%  | 1.18       │
│       1.0│ ●  ●      │  Buy Hold  | 22.1%  | 0.95       │
│       0.5│●          │  ...                              │
│         └──────→     │                                   │
│       Total Return   │                                   │
│                      │                                   │
└──────────────────────┴──────────────────────────────────┘
```

### Key Visualizations

#### 1. Total Return Bar Chart (Horizontal)
- **Rows**: Strategy Name
- **Columns**: Total Return %
- **Color**: Strategy Type (Momentum, Mean Reversion, etc.)
- **Sort**: Descending by return
- **Calculation**: Use `total_return_pct` field

#### 2. Risk/Return Scatter Plot
- **Rows**: Sharpe Ratio
- **Columns**: Total Return %
- **Color**: Strategy Name
- **Size**: Total Trades (larger = more active)
- **Label**: Strategy Name
- **Tooltip**: Include Max Drawdown, Win Rate

**Calculated Field - Quadrant Lines:**
```tableau
// Risk-Free Rate Line (Sharpe = 0)
IF [Sharpe Ratio] = 0 THEN [Total Return %] END

// Average Return Line
IF [Total Return %] = WINDOW_AVG([Total Return %]) THEN [Sharpe Ratio] END
```

#### 3. Performance Metrics Table
- **Rows**: Strategy Name, Ticker Symbol
- **Columns**: Total Return %, Annualized Return %, Sharpe Ratio, Max Drawdown %, Win Rate %
- **Color**: Conditional formatting (green for good, red for poor)
- **Sort**: By Sharpe Ratio descending

**Conditional Formatting Rules:**
- Return > 20%: Green
- Return 0-20%: Yellow
- Return < 0%: Red
- Sharpe > 1.0: Green
- Max Drawdown < -20%: Red

### Filters
- **Asset Type**: Stock / Crypto (multi-select)
- **Ticker Symbol**: All tickers (multi-select)
- **Strategy Name**: All strategies (multi-select)
- **Time Period**: Date range filter

### Actions
- Click on strategy → highlights across all charts
- Click on ticker → shows only that asset's performance

---

## Dashboard 2: Equity Curve Analysis

**Purpose**: Visualize portfolio value over time for selected strategies.

### Data Source
Connect to `vw_daily_strategy_performance`

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  SELECT TICKER: [AAPL ▼]                                │
│  SELECT STRATEGIES: [☑ Buy Hold] [☑ SMA] [☐ Bollinger] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📈 Equity Curves (Line Chart)                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Portfolio Value ($)                                     │
│      14,000 │              ╱─────                        │
│             │            ╱                               │
│      12,000 │       ────╱        ← SMA Crossover        │
│             │     ╱                                      │
│      10,000 │────────────────    ← Buy & Hold           │
│             │                                            │
│       8,000 └────────────────────────────────→          │
│                    Trade Date                            │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📉 Drawdown Chart (Area Chart)                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│       0% │────────────────────────                      │
│          │        ╲                                      │
│      -5% │         ╲    ╱                               │
│          │          ╲  ╱                                │
│     -10% │           ╲╱                                 │
│          │                                               │
│     -15% │                ← Max Drawdown                │
│          └───────────────────────────→                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Key Visualizations

#### 1. Equity Curve Line Chart
- **Rows**: Portfolio Value
- **Columns**: Trade Date (continuous)
- **Color**: Strategy Name
- **Filters**: Ticker Symbol (single select)

**Calculated Field - Cumulative Return %:**
```tableau
(SUM([Portfolio Value]) - 10000) / 10000 * 100
```

**Dual Axis Option**: Overlay price chart
- **Primary Axis**: Portfolio Value
- **Secondary Axis**: Close Price (right axis)

#### 2. Drawdown Area Chart
- **Rows**: Drawdown %
- **Columns**: Trade Date
- **Color**: Strategy Name (same as equity curve)
- **Mark Type**: Area

**Calculated Field - Drawdown:**
```tableau
// Running Max
RUNNING_MAX(SUM([Portfolio Value]))

// Drawdown %
(SUM([Portfolio Value]) - RUNNING_MAX(SUM([Portfolio Value]))) 
/ RUNNING_MAX(SUM([Portfolio Value])) * 100
```

### Advanced Features

**Reference Lines:**
- Starting capital line (y = $10,000)
- Max drawdown threshold (y = -20%)

**Annotations:**
- Mark maximum drawdown point
- Highlight major market events (if date table includes)

---

## Dashboard 3: Trade Analysis

**Purpose**: Analyze individual trades and patterns.

### Data Source
Connect to `vw_all_trades`

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  📊 Trade Distribution (Histogram)                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Frequency                                               │
│      25 │     ▄▄▄                                        │
│      20 │   ▄▄███▄▄                                      │
│      15 │  ▄███████▄                                     │
│      10 │▄▄█████████▄▄                                   │
│       0 └────────────────────→                          │
│           -10%  0%  +10%  +20%                          │
│              Trade Return %                              │
│                                                          │
├──────────────────────┬──────────────────────────────────┤
│                      │                                   │
│  📅 Holding Period   │  💰 Win/Loss Analysis            │
│     Box Plot         │                                   │
│                      │  Metric      | Value             │
│    Days Held         │  ─────────────────────           │
│      100│     ●       │  Avg Win     | +5.2%            │
│       80│   ┌─┴─┐     │  Avg Loss    | -3.1%            │
│       60│   │   │     │  Win/Loss    | 1.68             │
│       40│   │   │     │  Profit Fac  | 2.14             │
│       20│ ──└───┘     │  Expectancy  | +1.8%            │
│        0└────────     │                                   │
│                      │                                   │
└──────────────────────┴──────────────────────────────────┘
```

### Key Visualizations

#### 1. Trade Return Distribution (Histogram)
- **Rows**: COUNT(Trade ID)
- **Columns**: Trade Return % (bins)
- **Color**: Win (green) vs Loss (red)

**Calculated Field - Win/Loss:**
```tableau
IF [Trade Return %] > 0 THEN "Win"
ELSE "Loss"
END
```

**Bin Settings:**
- Size: 2%
- Range: -30% to +30%

#### 2. Holding Period Box Plot
- **Rows**: Holding Days
- **Columns**: Strategy Name
- **Chart Type**: Box-and-Whisker
- Shows: Min, Q1, Median, Q3, Max, Outliers

#### 3. Win/Loss Summary Table
- **Calculated Fields**:

```tableau
// Average Win
IF [Trade Return %] > 0 THEN [Trade Return %] END
AVG(...)

// Average Loss
IF [Trade Return %] <= 0 THEN [Trade Return %] END
AVG(...)

// Win/Loss Ratio
[Avg Win] / ABS([Avg Loss])

// Profit Factor
SUM(IF [Trade Return Dollars] > 0 THEN [Trade Return Dollars] END)
/
ABS(SUM(IF [Trade Return Dollars] <= 0 THEN [Trade Return Dollars] END))

// Expectancy
([Win Rate] * [Avg Win]) + ((1 - [Win Rate]) * [Avg Loss])
```

---

## Dashboard 4: Asset Comparison

**Purpose**: Compare performance of stocks vs cryptocurrencies.

### Visualizations

1. **Volatility Comparison** (Bar Chart)
   - Show annualized volatility by asset
   - Group by asset type

2. **Correlation Heatmap** (Highlight Table)
   - Rows: Ticker
   - Columns: Ticker
   - Color: Correlation coefficient (-1 to +1)

3. **Volume Trends** (Line Chart)
   - Average daily volume over time
   - Separate lines for each asset type

---

## Calculated Fields Library

### Essential Calculations

**1. Cumulative Return**
```tableau
(SUM([Portfolio Value]) - [Starting Capital]) / [Starting Capital] * 100
```

**2. Sharpe Ratio** (if not pre-calculated)
```tableau
([Annualized Return %] - 0.02) / [Volatility]
```

**3. Max Drawdown**
```tableau
(SUM([Portfolio Value]) - RUNNING_MAX(SUM([Portfolio Value]))) 
/ RUNNING_MAX(SUM([Portfolio Value])) * 100
```

**4. Win Rate**
```tableau
COUNTD(IF [Trade Return %] > 0 THEN [Trade ID] END) 
/ 
COUNTD([Trade ID])
```

**5. Best/Worst Trade**
```tableau
// Best
WINDOW_MAX(MAX([Trade Return %]))

// Worst
WINDOW_MIN(MIN([Trade Return %]))
```

**6. Trade Expectancy**
```tableau
([Win Rate] * [Avg Win %]) + ((1 - [Win Rate]) * [Avg Loss %])
```

---

## Color Palettes

### Strategy Type Colors
- **Momentum**: Blue (#4472C4)
- **Mean Reversion**: Orange (#ED7D31)
- **Volatility**: Green (#70AD47)
- **Volume**: Purple (#7030A0)
- **Baseline**: Gray (#A5A5A5)

### Performance Colors
- **Positive Returns**: Green gradient
- **Negative Returns**: Red gradient
- **Neutral**: Gray

---

## Dashboard Best Practices

### Design Principles
1. **F-Pattern Layout**: Most important viz top-left
2. **Mobile-First**: Design for tablet viewing
3. **3-Click Rule**: Any insight within 3 clicks
4. **Consistent Filters**: Same filters across all dashboards

### Performance Optimization
1. Use **extracts** instead of live connections for faster loading
2. Aggregate data at the database level (use views)
3. Limit to 1 year of data by default (user can expand)
4. Avoid calculated fields in large datasets (pre-compute in SQL)

### Interactivity
1. **Filter Actions**: Click on one chart → filters all others
2. **Highlight Actions**: Hover to highlight related data
3. **URL Actions**: Link to strategy documentation
4. **Tooltips**: Include all relevant context

---

## Publishing to Tableau Public

### Steps
1. **File → Save to Tableau Public As...**
2. Sign in to Tableau Public account
3. Name: "Trading Strategy Backtest Analysis"
4. Add description and tags
5. Set privacy: Public or Unlisted

### Embedding
```html
<div class='tableauPlaceholder'>
  <object class='tableauViz' width='1000' height='800'>
    <param name='host_url' value='https://public.tableau.com/' />
    <param name='embed_code_version' value='3' />
    <param name='site_root' value='' />
    <param name='name' value='YourWorkbookName/Dashboard1' />
  </object>
</div>
```

---

## Troubleshooting

### Common Issues

**Problem**: Tableau can't connect to SQL Server
- **Solution**: Enable TCP/IP in SQL Server Configuration Manager
- **Solution**: Check firewall allows port 1433

**Problem**: Slow dashboard performance
- **Solution**: Create a Tableau extract (.hyper file)
- **Solution**: Use aggregated views instead of raw tables
- **Solution**: Apply context filters on date/ticker

**Problem**: Calculated field errors
- **Solution**: Check for NULL values (use IFNULL())
- **Solution**: Verify table join relationships
- **Solution**: Use table calculations instead of row-level calculations

---

## Resources

- [Tableau Public Gallery](https://public.tableau.com/app/discover) - Inspiration
- [Tableau Documentation](https://help.tableau.com/) - Official docs
- [SQL Server Connector Guide](https://help.tableau.com/current/pro/desktop/en-us/examples_sqlserver.htm)

---

*For questions about specific dashboard implementations, refer to the saved Tableau workbook (.twbx file) in the project repository.*
