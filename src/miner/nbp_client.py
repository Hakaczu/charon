import httpx
import logging
from datetime import date, timedelta
from typing import List, Dict, Optional, Any
import asyncio

logger = logging.getLogger(__name__)

class NBPClient:
    BASE_URL = "http://api.nbp.pl/api"
    MAX_DAYS_RANGE = 93 # NBP API limit

    async def fetch_exchange_rates(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Fetches exchange rates (Table A) handling the 93-day limit by splitting requests.
        """
        all_rates = []
        current_start = start_date

        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=self.MAX_DAYS_RANGE), end_date)
            
            url = f"{self.BASE_URL}/exchangerates/tables/A/{current_start}/{current_end}/"
            logger.info(f"Fetching rates from {url}")
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers={"Accept": "application/json"})
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Flatten the structure: one rate = one dict with effectiveDate
                        for entry in data:
                            eff_date = entry['effectiveDate']
                            for rate in entry['rates']:
                                rate['effectiveDate'] = eff_date
                                all_rates.append(rate)
                    elif response.status_code == 404:
                        logger.warning(f"No data found for range {current_start} to {current_end}")
                    else:
                        logger.error(f"Error fetching rates: {response.status_code} - {response.text}")
            
            except Exception as e:
                logger.error(f"Request failed: {e}")

            current_start = current_end + timedelta(days=1)
            await asyncio.sleep(0.1) # Be nice to the API

        return all_rates

    async def fetch_gold_prices(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Fetches gold prices handling the limit.
        """
        all_prices = []
        current_start = start_date

        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=self.MAX_DAYS_RANGE), end_date)
            
            url = f"{self.BASE_URL}/cenyzlota/{current_start}/{current_end}"
            logger.info(f"Fetching gold from {url}")
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers={"Accept": "application/json"})
                    
                    if response.status_code == 200:
                        data = response.json()
                        all_prices.extend(data)
                    elif response.status_code == 404:
                        logger.warning(f"No gold data found for range {current_start} to {current_end}")
                    else:
                        logger.error(f"Error fetching gold: {response.status_code} - {response.text}")

            except Exception as e:
                logger.error(f"Request failed: {e}")

            current_start = current_end + timedelta(days=1)
            await asyncio.sleep(0.1)

        return all_prices
