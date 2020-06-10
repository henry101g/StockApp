import yfinance as yf

st = yf.Ticker("KO")



# get stock info

print(st.info['longName'])
print(st.info['regularMarketPrice'])

# get historical market data, here max is 5 years.
#msft.history(period="max")
