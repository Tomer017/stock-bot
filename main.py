import robin_stocks.robinhood as rh
import pandas as pd
import json
import os
import time
import logging
import trading_strategies as ts

# Configure logging
logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Login to Robinhood
def login_to_robinhood():
    if os.path.exists("login_data.json"):
        with open('login_data.json', 'r') as file:
            try:
                login_data = json.load(file)
                username = login_data['username']
                password = login_data['password']
                try:
                    rh.login(username, password)
                    print("Login successful")
                    logging.info("Logged in to Robinhood.")
                    return
                except Exception as e:
                    print(f"An error occurred during login: {e}")
                    logging.error(f"Login error: {e}")
            except json.JSONDecodeError:
                print("login_data.json is empty or not properly formatted.")
                logging.error("login_data.json is empty or not properly formatted.")
    try:
        username = input('Enter your username: ')
        password = input('Enter your password: ')
        if input("Would you like to save your login details? (y/n): ").lower() == 'y':
            login_data = {
                'username': username,
                'password': password
            }
            with open('login_data.json', 'w') as file:
                json.dump(login_data, file)
        print("Logging in...")
        rh.login(username, password)
        print("Login successful")
        logging.info("Logged in to Robinhood.")
    except Exception as e:
        print(f"An error occurred during login: {e}")
        logging.error(f"Login error: {e}")

# Logout of Robinhood
def logout_of_robinhood():
    try:
        rh.logout()
        print("Logout successful")
        logging.info("Logged out of Robinhood.")
    except Exception as e:
        print(f"An error occurred during logout: {e}")
        logging.error(f"Logout error: {e}")

def manage_stocks_in_watchlist(watchlist_name):
    try:
        # Fetch all existing watchlists
        all_watchlists_response = rh.get_all_watchlists()
        
        # Ensure the response is properly parsed
        if isinstance(all_watchlists_response, str):
            all_watchlists_response = json.loads(all_watchlists_response)
        
        # Extract watchlist names
        watchlist_names = [watchlist['display_name'] for watchlist in all_watchlists_response['results']]
        
        # Check if the given watchlist exists
        if watchlist_name not in watchlist_names:
            print(f"Watchlist '{watchlist_name}' does not exist. Create it in the app.")
            return []
        
        # Fetch items in the specified watchlist
        watchlist_items = rh.get_watchlist_by_name(name=watchlist_name)
        if isinstance(watchlist_items, str):
            watchlist_items = json.loads(watchlist_items)
        
        # Extract symbols from the watchlist items
        watchlist_stocks = [item['symbol'] for item in watchlist_items['results']]
        
        print(f"Current stocks in watchlist '{watchlist_name}': {watchlist_stocks}")
        
        print("Would you like to change the stocks in your watchlist? (y/n)")
        if input().lower() == 'y':
            check1 = input("Would you like to remove any stocks from the watchlist? (y/n) ")
            if check1.lower() == 'y':
                stocks_to_remove = input('Enter the stock symbols to remove (separated by commas): ').split(',')
                for stock in stocks_to_remove:
                    stock = stock.strip().upper()
                    try:
                        rh.delete_symbols_from_watchlist(stock, name=watchlist_name)
                        print(f"Stock {stock} removed from watchlist {watchlist_name}")
                    except Exception as e:
                        print(f"An error occurred while removing stock {stock} from watchlist: {e}")
                
                # Update watchlist_stocks after removing stocks
                watchlist_items = rh.get_watchlist_by_name(name=watchlist_name)
                if isinstance(watchlist_items, str):
                    watchlist_items = json.loads(watchlist_items)
                watchlist_stocks = [item['symbol'] for item in watchlist_items['results']]
                print(f"Updated stocks in watchlist '{watchlist_name}': {watchlist_stocks}")
            elif check1.lower() == 'n':
                check2 = input("Would you like to add new stocks to the watchlist? (y/n)")
                if check2.lower() == 'y':
                    new_stocks = input('Enter the stock symbols to add (separated by commas): ').split(',')
                    for stock in new_stocks:
                        stock = stock.strip().upper()
                        try:
                            rh.post_symbols_to_watchlist(stock, name=watchlist_name)
                            print(f"Stock {stock} added to watchlist {watchlist_name}")
                        except Exception as e:
                            print(f"An error occurred while adding stock {stock} to watchlist: {e}")
            else:
                 # Update watchlist_stocks after adding new stocks
                watchlist_items = rh.get_watchlist_by_name(name=watchlist_name)
                if isinstance(watchlist_items, str):
                    watchlist_items = json.loads(watchlist_items)
                watchlist_stocks = [item['symbol'] for item in watchlist_items['results']]          
        
        return watchlist_stocks
    except Exception as e:
        print(f"An error occurred while managing watchlist: {e}")
        return []

# Validate stock symbol
def validate_stock_symbol(stock_symbol):
    try:
        quote = rh.stocks.get_stock_quote_by_symbol(stock_symbol)
        if quote and 'symbol' in quote:
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred while validating stock symbol {stock_symbol}: {e}")
        logging.error(f"Error validating stock symbol {stock_symbol}: {e}")
        return False

# Get historical data for a stock
def get_stock_historical_data(stock_symbol, interval, span):
    try:
        if not validate_stock_symbol(stock_symbol):
            raise ValueError(f"Invalid stock symbol: {stock_symbol}")
        historical_data = rh.stocks.get_stock_historicals(stock_symbol, interval=interval, span=span, bounds='regular')
        if not historical_data:
            raise ValueError("No historical data returned")
        df = pd.DataFrame(historical_data)
        if 'begins_at' not in df.columns:
            raise ValueError(f"'begins_at' column not found in the data for {stock_symbol}")
        df.set_index('begins_at', inplace=True)
        df.rename(columns={
            'open_price': 'Open',
            'high_price': 'High',
            'low_price': 'Low',
            'close_price': 'Close'
        }, inplace=True)
        # Convert price columns to float
        for col in ['Open', 'High', 'Low', 'Close']:
            df[col] = df[col].astype(float)
        return df
    except Exception as e:
        print(f"An error occurred while fetching historical data for {stock_symbol}: {e}")
        logging.error(f"Error fetching historical data for {stock_symbol}: {e}")
        return None

# Execute trade based on trading decision
def execute_trade(stock_symbol, amount, trade_action):
    try:
        if trade_action in ['buy', 'sell']:
            logging.info(f"Signal detected for {stock_symbol}: {trade_action.upper()}")
            confirmation = input(f"Do you want to {trade_action} {stock_symbol} for ${amount}? (y/n): ")
            if confirmation.lower() == 'y':
                if trade_action == 'buy':
                    rh.orders.order_buy_fractional_by_price(stock_symbol, amount)
                elif trade_action == 'sell':
                    rh.orders.order_sell_fractional_by_price(stock_symbol, amount)
                print(f"Trade executed: {trade_action} {stock_symbol} for ${amount}")
                logging.info(f"Trade executed: {trade_action} {stock_symbol} for ${amount}")
            else:
                print("Trade canceled")
                logging.info(f"Trade canceled for {stock_symbol}")
        else:
            print(f"No trade action required for {stock_symbol}.")
            logging.info(f"No action for {stock_symbol}")
    except Exception as e:
        print(f"An error occurred while executing trade: {e}")
        logging.error(f"Error executing trade for {stock_symbol}: {e}")

# View portfolio
def view_portfolio():
    try:
        portfolio = rh.profiles.load_portfolio_profile()
        print(portfolio)
        logging.info(f"Portfolio: {portfolio}")
    except Exception as e:
        print(f"An error occurred while fetching portfolio: {e}")
        logging.error(f"Error fetching portfolio: {e}")

# Main function
def main():
    login_to_robinhood()
    watchlist_name = input('Enter the name of the watchlist you want to use: ')
    watchlist_stocks = manage_stocks_in_watchlist(watchlist_name)
    if not watchlist_stocks:
        print("No stocks in watchlist. Exiting.")
        logging.info("No stocks in watchlist. Exiting.")
        logout_of_robinhood()
        return
    amount = float(input('Enter the amount to trade per stock (in dollars): $'))
    refresh_interval = int(input('Enter the refresh interval in seconds: '))
    # Strategy selection
    print("Select a trading strategy:")
    print("1. Heikin-Ashi")
    print("2. SMA Crossover")
    strategy_choice = input("Enter the number of your choice: ")
    if strategy_choice == '1':
        strategy = 'heikin_ashi'
    elif strategy_choice == '2':
        strategy = 'sma_crossover'
    else:
        print("Invalid choice. Exiting.")
        logging.error("Invalid strategy choice.")
        logout_of_robinhood()
        return
    print("Monitoring stocks. Press Ctrl+C to exit.")
    logging.info(f"Started monitoring stocks with strategy: {strategy}")
    try:
        while True:
            for stock in watchlist_stocks:
                stock = stock.strip().upper()
                df = get_stock_historical_data(stock, '5minute', 'month')
                if df is None or df.empty:
                    print(f"No data for {stock}. Skipping.")
                    logging.warning(f"No data for {stock}. Skipping.")
                    continue
                if strategy == 'heikin_ashi':
                    indicator_df = ts.calculate_heikin_ashi(df)
                    trade_action = ts.trading_decision_heikin_ashi(indicator_df)
                elif strategy == 'sma_crossover':
                    indicator_df = ts.calculate_sma(df)
                    trade_action = ts.trading_decision_sma(indicator_df)
                elif strategy == 'news_sentiment_analysis':
                    news_df = ts.get_news_sentiment(stock)
                    trade_action = ts.trading_decision_nsa(news_df)
                if trade_action != 'hold':
                    print(f"Trading signal for {stock}: {trade_action.upper()}")
                    execute_trade(stock, amount, trade_action)
                else:
                    print(f"No action for {stock}.")
                    logging.info(f"No action for {stock}.")
                # Sleep briefly to avoid hitting API rate limits
                time.sleep(1)
            print(f"Waiting for {refresh_interval} seconds before next check...")
            time.sleep(refresh_interval)
    except KeyboardInterrupt:
        print("Stopping monitoring.")
        logging.info("Monitoring stopped by user.")
    finally:
        logout_of_robinhood()

if __name__ == "__main__":
    main()