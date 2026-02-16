import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Shop1989ND:
    def __init__(self, username, password, timeout=15):
        self.domain = "https://www.shop1989nd.com"
        self.username = username
        self.password = password
        self.timeout = timeout

        # Tạo session có retry
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

    def buy_resource(self, product_id: int, amount: int = 1):
        """
        Mua tài nguyên từ đối tác
        """
        url = f"{self.domain}/api/BResource.php"

        params = {
            "username": self.username,
            "password": self.password,
            "id": product_id,
            "amount": amount
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            try:
                return response.json()
            except ValueError:
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "raw": response.text
                }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def extract_email_pass(self, response_json):
        """
        Lọc email|password từ response API
        """
        results = []

        if response_json.get("status") != "success":
            return results

        lists = response_json.get("data", {}).get("lists", [])

        for item in lists:
            raw_account = item.get("account", "")
            parts = raw_account.split("|")

            if len(parts) >= 2:
                email = parts[0].strip()
                password = parts[1].strip()
                results.append(f"{email}|{password}")

        return results
    
    def buy_email(self, amount: int = 1):
        """
        Shortcut mua email (ID = 19)
        """
        return self.buy_resource(product_id=19, amount=amount)