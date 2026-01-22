import os
import asyncio
import logging
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from bring_api import BringClient
import aiohttp
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ShoppingItem:
    name: str
    quantity: float
    unit: str
    original: str = ""

class Config:
    def __init__(self):
        self.mealie_base = os.getenv('MEALIE_BASE_URL', 'http://localhost:9000')
        self.mealie_token = os.getenv('MEALIE_TOKEN', '')
        self.mealie_list_id = os.getenv('MEALIE_SHOPPING_LIST_ID', 'default')
        self.bring_user = os.getenv('BRING_USERNAME', '')
        self.bring_pass = os.getenv('BRING_PASSWORD', '')
        self.bring_list_name = os.getenv('BRING_LIST_NAME', 'Einkauf')
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        # Unit mapping
        raw_mapping = os.getenv('UNITS_MAPPING', 
            '{"g":"g","kg":"kg","ml":"ml","l":"L","Stück":"Stk.","TL":"TL","EL":"EL","Prise":"Prise"}')
        self.units = json.loads(raw_mapping)

config = Config()

def parse_quantity_unit(text: str) -> Optional[Dict]:
    """1.5kg Äpfel → {'quantity':1.5, 'unit':'kg', 'name':'Äpfel'}"""
    # Zahl + Einheit + Rest
    pattern = r'^(\d+(?:[.,]\d+)?)\s*([a-zA-ZäöüÄÖÜ]+)\s+(.*)$'
    match = re.match(pattern, text, re.IGNORECASE)
    if match:
        qty = float(match.group(1).replace(',', '.'))
        unit = match.group(2).lower()
        name = match.group(3).strip()
        return {'quantity': qty, 'unit': unit, 'name': name}
    return None

async def fetch_mealie_items() -> List[ShoppingItem]:
    """Real Mealie API call"""
    url = f"{config.mealie_base}/api/shopping-lists/{config.mealie_list_id}/items"
    headers = {"Authorization": f"Token {config.mealie_token}"}
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    logger.error(f"Mealie API {resp.status}: {await resp.text()}")
                    return []
                
                data = await resp.json()
                items = []
                
                for item in data.get('items', []):
                    name = item.get('name', '').strip()
                    
                    # Try structured fields first
                    qty = float(item.get('quantity', 1) or 1)
                    unit = item.get('unit', '') or ''
                    
                    # Fallback: parse unstructured name
                    if not unit or qty == 1:
                        parsed = parse_quantity_unit(name)
                        if parsed:
                            name = parsed['name']
                            qty = parsed['quantity']
                            unit = parsed['unit']
                    
                    if name:
                        items.append(ShoppingItem(name, qty, unit, item.get('name')))
                
                logger.info(f"✅ Mealie: {len(items)} Items geladen")
                return items
    except Exception as e:
        logger.error(f"❌ Mealie fetch failed: {e}")
        return []

async def push_to_bring(items: List[ShoppingItem]) -> List[str]:
    """Real Bring! API push"""
    if not config.bring_user or not confi
