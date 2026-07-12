# How to Run Your Binary Option OTC AI Trading Bot

## Prerequisites
1. **Python 3**: Ensure you have Python 3.7 or higher installed on your system.
2. **Telegram Bot**: You have already provided the bot token.
3. **Telegram Chat ID**: You need to find your Telegram Chat ID. You can do this by messaging [@userinfobot](https://t.me/userinfobot) on Telegram.

## Installation
1. Open your terminal or command prompt.
2. Install the required Python libraries using pip:
   ```bash
   pip install pandas ta python-telegram-bot
   ```

## Configuration
1. Open the `bot.py` file in a text editor.
2. Locate the line: `TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"`
3. Replace `"YOUR_CHAT_ID"` with your actual numeric Chat ID (e.g., `123456789`).

## Running the Bot
1. In your terminal, navigate to the directory where you saved the files.
2. Run the bot using the following command:
   ```bash
   python bot.py
   ```

## What the Bot Does
- **Analyzes OTC Market Data**: Simulates real-time candlestick data.
- **Identifies Patterns**: Looks for Bullish Engulfing, Bearish Engulfing, Hammer, and Shooting Star patterns.
- **Checks Momentum**: Uses the RSI (Relative Strength Index) to identify overbought/oversold conditions.
- **Evaluates Trends**: Uses the ADX (Average Directional Index) to determine trend strength.
- **Monitors Pressure**: Calculates buyer and seller pressure based on price action.
- **Sends Alerts**: When a high-probability setup is confirmed (pattern + RSI + ADX + Pressure), it sends a signal to your Telegram.

## Important Note
This bot is a simulation and uses simulated data. To use it with a real broker, you would need to integrate it with the broker's specific API (e.g., IQ Option, Pocket Option, etc.). Always test any trading strategy on a demo account before using real money.
