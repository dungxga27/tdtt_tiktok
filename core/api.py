import requests
from utils.logger import log_info, log_error


def request_api(url, method="GET", data=None, headers=None, retries=3, timeout=15):
    """
    Gửi request API đơn giản
    """

    session = requests.Session()

    for attempt in range(1, retries + 1):
        try:
            response = session.request(
                method=method,
                url=url,
                json=data if method.upper() != "GET" else None,
                params=data if method.upper() == "GET" else None,
                headers=headers,
                timeout=timeout,
            )

            response.raise_for_status()

            # nếu trả về JSON
            try:
                return response.json()
            except:
                return response.text

        except Exception as e:
            log_error(f"API lỗi (lần {attempt}/{retries}): {e}")

    return None
