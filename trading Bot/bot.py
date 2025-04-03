import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time 
from datetime import datetime, timedelta


# connect to exness
if not mt5.initialize():
    print("MT5 installation failed")
    mt5.shutdown()

# set trading parameters
SYMBOL = "BTCUSD"
LOT_SIZE = 0.01
ATR_PERIOD = 14
RISK_REWARD_RATIO = 1.5
DAILY_PROFIT_TARGET = 2.0
MAX_TRADES = 5
TIMEFRAME = mt5.TIMEFRAME_M1
ACCOUNT_CURRENCY = "USD"


# track daily profit
daily_profit = 0
trades_today = 0
last_trade_day = datetime.now().date()


# function to get historical data
def get_data(symbol, timeframe, bars=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# function to calculate atr
def calculate_atr(data, period=ATR_PERIOD):
    data['tr0'] = abs(data['high'] - data['low'])
    data['tr1'] = abs(data['high'] - data['close'].shift(1))
    data['tr2'] = abs(data['low'] - data['close'].shift(1))
    data['true_range'] = data[['tr0', 'tr1', 'tr2']].max(axis=1)
    data['atr'] = data['true_range'].rolling(period).mean()
    return data

# function to check daily profit target

def check_daily_limit():
    global daily_profit, trades_today, last_trade_day
    if datetime.now().date() != last_trade_day:
        # reset daily counter
        daily_profit = 0
        trades_today = 0
        last_trade_day = datetime.now().date()
    return daily_profit >= DAILY_PROFIT_TARGET or trades_today >= MAX_TRADES


# function to order placement
def place_trade(direction):
    global daily_profit, trades_today

    #Fetch latest ATR value
    data = get_data(SYMBOL, TIMEFRAME)
    data = calculate_atr(data)
    atr_value = data['atr'].iloc[-1]

    # define sl and tp based on atr
    sl_pips = atr_value * 1.5
    tp_pips = atr_value * RISK_REWARD_RATIO * 1.5

    price = mt5.symbol_info_tick(SYMBOL).ask if direction == "BUY" else mt5.symbol_info_tick(SYMBOL).bid
    sl = price - sl_pips if direction == "BUY" else price + sl_pips
    tp = price + tp_pips if direction == "BUY" else price - tp_pips


    # order structure
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        
    }
