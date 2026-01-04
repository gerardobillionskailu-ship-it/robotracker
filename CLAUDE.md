# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradeOlympo is a financial analysis application built with Streamlit that monitors stocks (CVX, SLB, HAL, XLE) and suggests options strategies for Cash accounts (Long Calls only, no spreads).

## Technology Stack

- **Framework**: Streamlit (web UI)
- **Data Source**: yfinance (market data)
- **Charting**: Plotly (interactive charts)
- **Analysis**: Pandas, NumPy, ta (technical analysis)

## Development Commands

### Setup
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Requirements
- Python 3.8 or higher
- Internet connection (for fetching market data via yfinance)

### Running the App
```bash
# Default run (opens in browser)
streamlit run app.py

# Specify port
streamlit run app.py --server.port 8501

# Disable file watching (for production)
streamlit run app.py --server.fileWatcherType none
```

## Architecture

### Application Structure

The app follows a modular architecture with separation of concerns:

**app.py** (Entry point)
- Streamlit page configuration and global settings
- Sidebar rendering with strategy mode selection (Larry Williams vs Wyckoff)
- Main application flow and error handling
- Integration point for views and utils modules

**views/dashboard.py** (UI Layer)
- Implements 3-column layout: Watchlist, Strategy Card, News
- **Dynamic Strategy Card**: Changes display based on selected strategy mode
- Renders different visualizations for Larry Williams vs Wyckoff strategies
- Chart rendering with strategy-specific indicators

**utils/indicators.py** (Business Logic)
- `TechnicalIndicators` class: Core indicator calculation engine
- **Larry Williams Strategy**: Williams %R, SMA crossovers (Golden/Death Cross)
- **Wyckoff Strategy**: Volume analysis, candle position analysis, accumulation/distribution detection
- Signal generation methods that return actionable trading signals

### Key Design Patterns

**Strategy Pattern**: The app switches between Larry Williams and Wyckoff analysis modes dynamically. Both strategies implement the same interface (`get_*_signal()` methods) but with different analysis logic.

**Session State Management**: Streamlit's session_state is used to maintain selected symbol across reruns.

**Separation of Concerns**:
- `utils/` contains pure calculation logic (no UI code)
- `views/` contains UI rendering logic (delegates calculations to utils)
- `app.py` orchestrates the flow but doesn't contain business logic

## Business Rules

### Account Type: Cash Only
- The application assumes a Cash account by default
- **Only suggests**: Direct Call purchases or stock purchases
- **Never suggests**: Vertical spreads, short positions, or margin strategies

### Wyckoff Volume Highlighting
- When volume exceeds 150% of the 20-period average, it is highlighted in the chart
- Color coding:
  - **Dark Green**: High volume + close in upper 70% (bullish strength)
  - **Dark Red**: High volume + close in lower 30% (bearish weakness)
  - **Orange**: High volume without clear direction

## Code Conventions

### Adding New Indicators

To add a new technical indicator:

1. Add calculation method to `utils/indicators.py`:
   ```python
   def calculate_new_indicator(self) -> pd.DataFrame:
       """Calculate new indicator and add to self.df"""
       self.df['new_indicator'] = ... # your calculation
       return self.df
   ```

2. Call it from `calculate_all_indicators()`:
   ```python
   def calculate_all_indicators(self) -> pd.DataFrame:
       self.calculate_larry_williams()
       self.calculate_wyckoff_metrics()
       self.calculate_new_indicator()  # Add here
       return self.df
   ```

3. Create signal generation method:
   ```python
   def get_new_indicator_signal(self) -> Dict[str, any]:
       """Returns dict with: signal, strength, reasons, suggested_strategy"""
   ```

4. Update `views/dashboard.py` to add new strategy mode option

### Adding New Symbols to Watchlist

Update the `WATCHLIST_SYMBOLS` constant in `views/dashboard.py`:
```python
WATCHLIST_SYMBOLS = ['CVX', 'SLB', 'HAL', 'XLE', 'NEW_SYMBOL']
```

## Data Flow

1. User selects strategy mode in sidebar (app.py)
2. User selects symbol in watchlist (views/dashboard.py)
3. Dashboard fetches historical data via yfinance
4. TechnicalIndicators calculates all indicators
5. Strategy-specific signal generation method is called
6. Results are rendered in strategy card with appropriate visualization
7. Chart is rendered with strategy-specific overlays

## Error Handling Philosophy

The app uses "graceful degradation":
- Network errors show friendly messages with retry suggestions
- Missing data for individual symbols doesn't crash the entire watchlist
- Detailed error information is available in expandable sections
- All data fetching is wrapped in try/except blocks

## Extending the Application

### To add a new strategy mode:

1. Add indicator calculations to `utils/indicators.py`
2. Create `get_[strategy]_signal()` method
3. Add rendering function in `views/dashboard.py`: `render_[strategy]_card()`
4. Update `render_strategy_card()` to handle new mode
5. Update `render_chart()` to add strategy-specific visualizations
6. Add new option to sidebar radio button in `app.py`

## Troubleshooting

### Common Issues

**"No module named 'streamlit'"**
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`

**"Unable to fetch data for symbol"**
- Check internet connection
- yfinance may have rate limits; wait a few seconds and retry
- Some symbols may not have historical data available

**Chart not rendering**
- Check browser console for JavaScript errors
- Try clearing browser cache
- Ensure Plotly is installed: `pip install plotly`

**Session state errors**
- Streamlit's session state is reset on page refresh
- Selected symbol defaults to first in watchlist (CVX)
