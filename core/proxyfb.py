import requests
import time
from utils.logger import log_info, log_error, log_warning

class ProxyFb:
    def __init__(self, key):
        self.key = key
        self.api_url = "http://api.proxyfb.com/api"
        self.current_proxy = None

    def get_prox(self):
        """
        Logic: Kiểm tra proxy hiện tại trước, nếu không có/lỗi thì đổi proxy mới.
        """
        # 1. Kiểm tra IP hiện tại
        log_info(f"[*] Đang kiểm tra trạng thái proxy cho key: {self.key}...")
        check_url = f"{self.api_url}/getProxy.php?key={self.key}"
        
        try:
            response = requests.get(check_url)
            res = response.json()

            if res.get("success"):
                timeout_val = int(res.get("timeout", 0))
                # Nếu còn thời gian sử dụng (> 10s) thì dùng tiếp
                if timeout_val > 10:
                    log_info(f"[+] Sử dụng proxy hiện tại: {res['proxy']} (Còn {res['timeout']}s)")
                    self.current_proxy = res['proxy']
                    return self.current_proxy
            
            # 2. Nếu không có proxy hoặc sắp hết hạn, tiến hành đổi IP mới
            log_warning("[!] Proxy cũ không sẵn dụng. Đang lấy IP mới...")
            change_url = f"{self.api_url}/changeProxy.php?key={self.key}"
            
            res_change = requests.get(change_url).json()
            if res_change.get("success"):
                log_info(f"[+] Đổi IP thành công: {res_change['proxy']}")
                self.current_proxy = res_change['proxy']
                return self.current_proxy
            else:
                # Trường hợp lỗi do chưa đến thời gian đổi (next_change)
                desc = res_change.get("description", "")
                log_error(f"[-] Thất bại: {desc}")
                
                # Nếu lỗi do đợi đổi IP, có thể lấy lại IP hiện tại để dùng tạm
                if "next_change" in desc or "please wait" in desc.lower():
                     return self.current_proxy # Trả về proxy cũ đã lưu trước đó nếu có
                
                return None

        except Exception as e:
            log_error(f"[-] Lỗi kết nối API ProxyFB: {e}")
            return None

    def get_locations(self):
        """Lấy danh sách các vị trí khả dụng"""
        try:
            res = requests.get(f"{self.api_url}/getLocations.php").json()
            return res
        except:
            return []