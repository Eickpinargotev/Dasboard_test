import requests
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class KeepconClient:
    def __init__(self, config):
        self.config = config
        self.last_error = ""

    def search_content(self, from_date, to_date, next_page_token=None):
        payload = {
            "sources": ["twitter", "facebook", "instagram"],
            "content_types": self.config.allowed_content_types,
            "created_at_from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "created_at_to": to_date.strftime("%Y-%m-%dT%H:%M:%S")
        }
        return self.search_content_payload(payload, next_page_token)

    def search_content_by_updated_at(self, from_date, to_date, next_page_token=None):
        payload = {
            "sources": ["twitter", "facebook", "instagram"],
            "content_types": self.config.allowed_content_types,
            "updated_at_from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "updated_at_to": to_date.strftime("%Y-%m-%dT%H:%M:%S")
        }
        return self.search_content_payload(payload, next_page_token)

    def search_content_payload(self, payload, next_page_token=None):
        self.last_error = ""
        if not self.config.token or not self.config.account_number:
            self.last_error = "No hay credenciales de Keepcon configuradas."
            logger.error(self.last_error)
            return None

        headers = {"Content-Type": "application/json"}
        url = f"{self.config.base_url}?access_token={self.config.token}"
        if next_page_token:
            url += f"&next_page_token={next_page_token}"

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code != 200:
                self.last_error = f"Keepcon API respondió {response.status_code}: {response.text}"
                logger.error(self.last_error)
                return None
            return response.json()
        except Exception as e:
            self.last_error = f"No se pudo conectar con Keepcon: {e}"
            logger.error(self.last_error)
            return None

    def get_content(self, content_id):
        self.last_error = ""
        if not self.config.token or not self.config.account_number or not content_id:
            self.last_error = "No hay credenciales de Keepcon o content_id para consultar contenido."
            logger.error(self.last_error)
            return None

        item_id = quote(str(content_id), safe="")
        url = f"https://api.keepcon.com/accounts/{self.config.account_number}/content/{item_id}?access_token={self.config.token}"

        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                self.last_error = f"Keepcon content/{content_id} respondió {response.status_code}: {response.text}"
                logger.warning(self.last_error)
                return None
            return response.json()
        except Exception as e:
            self.last_error = f"No se pudo consultar contenido Keepcon: {e}"
            logger.warning(self.last_error)
            return None

    def get_profile(self, social_network, social_user_id):
        if not self.config.token or not self.config.account_number or not social_user_id:
            return None

        network = quote(str(social_network or ""), safe="")
        user_id = quote(str(social_user_id), safe="")
        url = f"{self.config.profiles_url}/{network}/{user_id}?access_token={self.config.token}"

        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                logger.warning("Keepcon profile lookup failed: %s - %s", response.status_code, response.text)
                return None
            return response.json()
        except Exception as e:
            logger.warning("Error during Keepcon profile request: %s", e)
            return None
