from ib_async import IB, Stock, MarketOrder
import asyncio

async def run_first_trade():
    ib = IB()
    try:
        # Match the Port (4002) and IP (127.0.0.1) from your screenshots
        await ib.connectAsync('127.0.0.1', 4002, clientId=1)
        
        # Define a safe test contract (e.g., 1 share of SHY)
        contract = Stock('SHY', 'SMART', 'USD')
        await ib.qualifyContractsAsync(contract)
        
        # Place a small test order
        order = MarketOrder('BUY', 1)
        trade = ib.placeOrder(contract, order)
        
        print(f"Trade sent! Status: {trade.orderStatus.status}")
        
        # Give it a few seconds to fill
        await asyncio.sleep(3)
        print(f"Final Status: {trade.orderStatus.status}")
        
    finally:
        ib.disconnect()

if __name__ == "__main__":
    asyncio.run(run_first_trade())