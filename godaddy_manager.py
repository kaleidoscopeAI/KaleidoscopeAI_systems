import os
import logging
from typing import List
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DNSRecord:
    type: str
    name: str
    value: str
    ttl: int = 600

class GoDaddyManager:
    def __init__(self, api_key: str, api_secret: str):
        self.base_url = "https://api.godaddy.com/v1"
        self.headers = {
            "Authorization": f"sso-key {api_key}:{api_secret}",
            "Content-Type": "application/json"
        }
    
    def update_dns(self, domain: str, records: List[DNSRecord]):
        try:
            url = f"{self.base_url}/domains/{domain}/records"
            payload = [[{
                "data": record.value,
                "name": record.name,
                "ttl": record.ttl,
                "type": record.type
            }] for record in records]
            
            response = requests.put(url, json=payload, headers=self.headers)
            response.raise_for_status()
            logger.info(f"DNS records updated for {domain}")
            return True
        except Exception as e:
            logger.error(f"DNS update failed: {str(e)}")
            return False
