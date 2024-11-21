# Heikin-Ashi Strategy
def calculate_heikin_ashi(df):
    """
    Calculate Heikin-Ashi values.
    """
    ha_df = df.copy()
    ha_df['HA_Close'] = (ha_df['Open'] + ha_df['High'] + ha_df['Low'] + ha_df['Close']) / 4
    ha_df['HA_Open'] = ((ha_df['Open'].shift(1) + ha_df['Close'].shift(1)) / 2).fillna(
        (ha_df['Open'] + ha_df['Close']) / 2)
    ha_df['HA_High'] = ha_df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)
    return ha_df[['HA_Open', 'HA_High', 'HA_Low', 'HA_Close']]

def trading_decision_heikin_ashi(ha_df):
    """
    Make trading decisions based on Heikin-Ashi data.
    Returns: 'buy', 'sell', or 'hold'
    """
    latest = ha_df.iloc[-1]
    previous = ha_df.iloc[-2] if len(ha_df) > 1 else None

    if latest['HA_Close'] > latest['HA_Open'] and (previous is None or previous['HA_Close'] <= previous['HA_Open']):
        # Signal to BUY when a bullish candle follows a bearish or neutral candle
        return 'buy'
    elif latest['HA_Close'] < latest['HA_Open'] and (previous is None or previous['HA_Close'] >= previous['HA_Open']):
        # Signal to SELL when a bearish candle follows a bullish or neutral candle
        return 'sell'
    else:
        return 'hold'

# Simple Moving Average (SMA) Crossover Strategy
def calculate_sma(df, short_window=5, long_window=20):
    df['SMA_Short'] = df['Close'].rolling(window=short_window).mean()
    df['SMA_Long'] = df['Close'].rolling(window=long_window).mean()
    return df

def trading_decision_sma(df):
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else None

    if latest['SMA_Short'] > latest['SMA_Long'] and previous is not None and previous['SMA_Short'] <= previous['SMA_Long']:
        # Golden cross, signal to BUY
        return 'buy'
    elif latest['SMA_Short'] < latest['SMA_Long'] and previous is not None and previous['SMA_Short'] >= previous['SMA_Long']:
        # Death cross, signal to SELL
        return 'sell'
    else:
        return 'hold'

def news_sentiment_analysis(news_df):
    """
    Analyze news sentiment.
    Returns: 'positive', 'negative', or 'neutral'
    """
    sentiment_score = news_df['Sentiment'].mean()
    if sentiment_score > 0.1:
        return 'positive'
    elif sentiment_score < -0.1:
        return 'negative'
    else:
        return 'neutral'

def trading_decision_nsa(news_df):
    sentiment = news_sentiment_analysis(news_df)
    if sentiment == 'positive':
        return 'buy'
    elif sentiment == 'negative':
        return 'sell'
    else:
        return 'hold'