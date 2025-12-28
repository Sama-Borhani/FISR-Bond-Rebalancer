from ib_async import IB, Stock
import asyncio

async def get_market_data():
    ib = IB()
    try:
        # Connect to the IB Gateway (Default port 4001 for Paper Trading)
        await ib.connectAsync('127.0.0.1', 4001, clientId=1)
        
        # Define the ETFs
        contracts = [Stock(s, 'SMART', 'USD') for s in ['SHY', 'IEF', 'TLT']]
        
        # Qualify (Check if these tickers are valid)
        for c in contracts:
            await ib.qualifyContractsAsync(c)
            
        # Get live prices
        tickers = await ib.reqTickersAsync(*contracts)
        
        prices = {t.contract.symbol: t.marketPrice() for t in tickers}
        return prices
        
    finally:
        ib.disconnect()

if __name__ == "__main__":
    # Test the connection
    prices = asyncio.run(get_market_data())
    print(f"Live Market Prices: {prices}")
    