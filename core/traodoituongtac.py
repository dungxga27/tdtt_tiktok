from utils.colors import Color
from config import TDTT_TOKEN, TDTT_USER, TDTT_PASS
from utils.logger import log_info, log_error
from core.api import request_api
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium_stealth import stealth

CONFIG_UID_URL = (
    "https://proxy.scalar.com/"
    "?scalar_url=https://public.traodoituongtac.com/api/v2/config-uid"
)

class TraoDoiTuongTac:
    def __init__(self, userId=None, jobType=None):
        self.token = TDTT_TOKEN
        self.userId = userId
        self.jobType = jobType
        self.driver_tdtt = None

    def config_uid(self):
        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json",
            "origin": "https://client.scalar.com",
            "referer": "https://client.scalar.com/",
            "user-agent": "Mozilla/5.0",
            "x-api-version": "public_ver_1"
        }

        data = {
            "uidId": self.userId,
            "platform": "tiktok"
        }

        response = request_api(
            url=CONFIG_UID_URL,
            method="POST",
            data=data,
            headers=headers,
            retries=3
        )

        if not response:
            log_error("❌ Config UID thất bại (no response)")
            return None

        if not response.get("success"):
            log_error(f"❌ Config UID lỗi: {response.get('message')}")
            return None

        info = response.get("data", {})

        log_info("======================================")
        log_info(f"✅ Config thành công UID: {info.get('uid')}")
        log_info(f"📱 Platform: {info.get('platform')}")
        log_info(f"👤 Name: {info.get('name')}")
        log_info(f"🆔 ID: {info.get('id')}")
        log_info(f"👥 Followers: {info.get('follower_count')}")
        log_info(f"🆕 Is New Config: {response.get('isNewConfig')}")
        log_info("======================================")

        return info
    
    def get_job(self):
        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json",
            "origin": "https://client.scalar.com",
            "referer": "https://client.scalar.com/",
            "user-agent": "Mozilla/5.0",
            "x-api-version": "public_ver_1"
        }

        data = {
            "fields": "tiktok_like",
            "uidId": self.userId
        }

        response = request_api(
            url="https://proxy.scalar.com/?scalar_url=https%3A%2F%2Fpublic.traodoituongtac.com%2Fapi%2Fv2%2Fget-jobs",
            method="POST",
            data=data,
            headers=headers,
            retries=3
        )

        if not response:
            log_error(f"❌ [{self.userId}] Get job thất bại (no response)")
            return None

        if not response.get("success"):
            log_error(f"❌ [{self.userId}] Get job lỗi: {response.get('message')}")
            return None

        jobs = response.get("data", [])

        job_count = len(jobs)

        log_info("======================================")
        log_info(f"🎯 Nhận được {job_count} job")
        log_info("======================================")

        return jobs
    
    def report_job(self, job_id, is_success=True, note="Đã like thành công"):
        # URL này lấy từ đoạn code axios của bạn (đã qua proxy scalar)
        url = "https://proxy.scalar.com/?scalar_url=https%3A%2F%2Fpublic.traodoituongtac.com%2Fapi%2Fv2%2Freports"
        
        headers = {
            "accept": "*/*",
            "accept-language": "vi,en;q=0.9",
            "authorization": f"Bearer {self.token}", # Token của bạn
            "content-type": "application/json",
            "origin": "https://client.scalar.com",
            "referer": "https://client.scalar.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "x-api-version": "public_ver_1"
        }

        # Data phải khớp hoàn toàn với mẫu JSON trong axios
        data = {
            "field": "tiktok_like",
            "isSuccess": is_success,
            "isJobDie": False,
            "jobId": job_id,       # Lấy từ job nhận được
            "uidId": self.userId, # ID tài khoản tiktok của bạn (ví dụ: sieudeptrai047)
            "note": note
        }

        try:
            response = request_api(
                url=url,
                method="POST",
                data=data,
                headers=headers,
                retries=3
            )

            if response and response.get("success"):
                log_info(f"✅ Báo cáo Job {job_id} thành công!")
                return True
            else:
                msg = response.get("message") if response else "No response"
                log_error(f"❌ Báo cáo Job thất bại: {msg}")
                return False
        except Exception as e:
            log_error(f"⚠️ Lỗi khi gửi report: {e}")
            return False
    
    def get_coins(self):
        """
        Gửi yêu cầu nhận xu sau khi đã hoàn thành các job like.
        """
        # URL lấy từ code axios của bạn
        url = "https://proxy.scalar.com/?scalar_url=https%3A%2F%2Fpublic.traodoituongtac.com%2Fapi%2Fv2%2Fget-coins"
        
        headers = {
            "accept": "*/*",
            "accept-language": "vi,en;q=0.9",
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json",
            "origin": "https://client.scalar.com",
            "referer": "https://client.scalar.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "x-api-version": "public_ver_1"
        }

        # Data gửi đi: field là loại job, uidId là ID tiktok của bạn
        data = {
            "field": "tiktok_like",
            "uidId": self.userId  # Đảm bảo self.username là "sieudeptrai047" hoặc tương đương
        }

        try:
            log_info(f"💰 [{self.userId}] Đang gửi yêu cầu nhận xu...")
            response = request_api(
                url=url,
                method="POST",
                data=data,
                headers=headers,
                retries=3
            )

            if response and response.get("success"):
                mess = response.get("message", "Thành công")
                # Thông thường API trả về số xu nhận được trong mess hoặc data
                log_info(f"✅ [{self.userId}] Nhận xu thành công: {mess}")
                return True
            else:
                error_mess = response.get("message") if response else "Không có phản hồi"
                log_error(f"❌ [{self.userId}] Nhận xu thất bại: {error_mess}")
                return False
                
        except Exception as e:
            log_error(f"⚠️ Lỗi khi gọi get_coins: {e}")
            return False
    
    def _create_tdtt_driver(self):
        options = ChromeOptions()
        
        # 1. Các thiết lập ẩn danh cơ bản
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # 2. Tối ưu tốc độ: Tắt hình ảnh (tùy chọn)
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        # 3. Kích thước và vị trí (dựa trên index của luồng)
        options.add_argument("--window-size=500,700")
        # Đẩy sang bên phải để không vướng cửa sổ TikTok
        pos_x = 1000 + (self.index * 20) 
        pos_y = self.index * 30
        options.add_argument(f"--window-position={pos_x},{pos_y}")

        # Khởi tạo driver
        driver = webdriver.Chrome(options=options)

        # 4. Cấu hình Stealth - Đây là phần quan trọng để qua mặt Cloudflare
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        self.driver_tdtt = driver
        return driver
    
    def open_and_wait_cloudflare(self, url):
        log_info(f"[{self.userId}] Đang truy cập và kiểm tra Cloudflare...")
        self.driver_tdtt.get(url)
        
        # Đợi tối đa 40 giây để người dùng giải hoặc Cloudflare tự qua
        for _ in range(20): 
            title = self.driver_tdtt.title.lower()
            # Nếu title không còn các chữ đặc trưng của Cloudflare
            if "just a moment" not in title and "cloudflare" not in title:
                log_info(f"[{self.userId}] ✅ Đã vượt qua Cloudflare!")
                return True
            
            log_info(f"[{self.userId}] ⏳ Đang đợi xác minh Cloudflare...")
            time.sleep(2)
            
        return False
    
    def login_web(self):
        """Đăng nhập vào giao diện web TDTT"""
        if not self.driver_tdtt:
            self._create_tdtt_driver()

        if self.open_and_wait_cloudflare("https://web.traodoituongtac.com/login"):
        
            log_info(f"[{TDTT_USER}] 🔑 Đang đăng nhập web TDTT...")
            
            try:
                wait = WebDriverWait(self.driver_tdtt, 10)
                wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(TDTT_USER)
                self.driver_tdtt.find_element(By.NAME, "password").send_keys(TDTT_PASS)
                self.driver_tdtt.find_element(By.NAME, "submit").click()
                
                # Đợi login thành công (check xem có redirect về home không)
                time.sleep(2)
                if "login.php" in self.driver_tdtt.current_url:
                    log_error("❌ Đăng nhập TDTT thất bại! Kiểm tra lại user/pass.")
                    return False
                log_info(f"[{self.user_web}] ✅ Đăng nhập thành công.")
                return True
            except Exception as e:
                log_error(f"⚠️ Lỗi login web: {e}")
                return False