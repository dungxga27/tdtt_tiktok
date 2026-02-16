import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import log_info, log_error, log_warning
import requests
import os
from selenium.webdriver.common.keys import Keys
import random
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
from core.proxyfb import ProxyFb
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException
from core.shop1989nd import Shop1989ND

class TikTokResolver:

    running_ips = set()

    def __init__(self, index=1, proxy=None, username=None, password=None):
        self.index = index
        self.proxy = proxy
        self.driver = None
        self.username = username
        self.password = password
        self._create_driver()

    def _get_current_public_ip(self, proxy=None):
        """Lấy IP public hiện tại (có hoặc không có proxy)"""
        proxies = None
        if proxy:
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        try:
            # Dùng API ipify để lấy IP thật sự mà web sẽ nhìn thấy
            response = requests.get("https://api.ipify.org", proxies=proxies, timeout=10)
            return response.text if response.status_code == 200 else None
        except:
            return None
        
    def resolve_username(self, full_link):
        try:
            url = f"https://www.tiktok.com/oembed?url={full_link}"

            headers = {
                "user-agent": "Mozilla/5.0"
            }

            r = requests.get(url, headers=headers, timeout=15)

            if r.status_code != 200:
                print("Status:", r.status_code)
                return None

            data = r.json()

            return data.get("author_unique_id")

        except Exception as e:
            print("Lỗi:", e)
            return None
        
    def _get_current_public_ip(self, ip_port=None):
        """Kiểm tra IP thực tế qua Proxy hoặc mạng máy"""
        proxies = None
        if ip_port:
            proxies = {"http": f"http://{ip_port}", "https": f"http://{ip_port}"}
        try:
            # Dùng trang này để check IP thật mà TikTok thấy
            response = requests.get("https://api.ipify.org", proxies=proxies, timeout=10)
            return response.text if response.status_code == 200 else None
        except:
            return None

    def _create_driver(self):
        # 1. LẤY PROXY
        proxy_service = ProxyFb(key=self.proxy)
        ip_port = proxy_service.get_prox()

        # 2. KIỂM TRA IP THỰC TẾ & TRÙNG LẶP
        actual_ip = self._get_current_public_ip(ip_port)
        
        if not actual_ip:
            print(f"[-] Luồng {self.index}: Không thể xác định IP. Kiểm tra kết nối mạng!")
            # Bạn có thể return None nếu muốn dừng luôn khi IP lỗi
        
        if actual_ip in self.running_ips:
            print(f"[!] Luồng {self.index}: CẢNH BÁO trùng IP ({actual_ip})!")
            # Nếu muốn chặn tuyệt đối trùng, bỏ comment dòng dưới:
            # return None 
        else:
            self.running_ips.add(actual_ip)
            self.current_ip = actual_ip # Lưu lại để lúc quit thì xóa khỏi set
            print(f"[+] Luồng {self.index} sử dụng IP: {actual_ip}")

        # 3. CẤU HÌNH CHROME OPTIONS
        options = ChromeOptions()
        
        # Logic sắp xếp cửa sổ
        width, height = 800, 600
        cols = 4
        row = (self.index - 1) // cols
        col = (self.index - 1) % cols
        pos_x = col * width
        pos_y = row * (height + 30)

        options.add_argument(f"--window-size={width},{height}")
        options.add_argument(f"--window-position={pos_x},{pos_y}")

        # Profile path
        profile_path = os.path.abspath(f"profiles/{self.username}")
        os.makedirs(profile_path, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")

        try:
            ua = UserAgent(use_external_data=False)
            desktop_agents = []

            for _ in range(20):
                candidate = ua.random
                if "Windows NT" in candidate or "Macintosh" in candidate:
                    if "Mobile" not in candidate:
                        desktop_agents.append(candidate)

            if desktop_agents:
                random_ua = random.choice(desktop_agents)
            else:
                raise Exception("No desktop UA found")

        except:
            random_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

        options.add_argument(f"user-agent={random_ua}")

        if ip_port:
            options.add_argument(f'--proxy-server=http://{ip_port}')

        # 4. KHỞI TẠO DRIVER
        try:
            self.driver = webdriver.Chrome(options=options)

            # Xóa dấu vết WebDriver bằng script CDP
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })

            # self.driver.get('https://checkip.com.vn/')

            # Truy cập TikTok với thời gian chờ ngẫu nhiên
            self.driver.get('https://www.tiktok.com/')

            time.sleep(random.uniform(3, 8))
            self.driver.execute_script("window.scrollBy(0, 500)")

            if "403" in self.driver.title or "Access Denied" in self.driver.page_source:
                    log_error(f"[-] Luồng {self.index}: IP {actual_ip} bị 403. Đang đổi IP khác...")
                    # Giải phóng IP lỗi khỏi danh sách chạy (nếu có)
                    if actual_ip in self.running_ips:
                        self.running_ips.remove(actual_ip)
                        proxy_service.current_proxy
                    
                    self.driver.quit()
                    self.driver = None
            
            time.sleep(random.uniform(2, 5)) 
            
            return self.driver
        except Exception as e:
            print(f"[-] Luồng {self.index} lỗi khởi tạo: {e}")
            if self.current_ip in self.running_ips:
                self.running_ips.remove(self.current_ip)
            return None

    def wait_for_login_button(self, timeout=20):
        try:
            print(f"[*] Luồng {self.index}: Đang đợi nút Login xuất hiện...")
            
            # Thiết lập đợi tối đa 'timeout' giây
            wait = WebDriverWait(self.driver, timeout)
            
            # Đợi cho đến khi phần tử hiện diện và có thể click được
            xpath_login = '//*[@id="top-right-action-bar-login-button"]/div/div'
            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_login)))
            login_btn.click()

            time.sleep(1)

            xpath_login_div = '//*[@id="loginContainer"]/div[1]/div/div/div/div/div[2]/div[2]/div[2]/div'
            login_btn_div = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_login_div)))
            login_btn_div.click()

            #
            xpath_emailOrUser = '//*[@id="loginContainer"]/div[2]/div/div/div/a'
            login_emailOrUser = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_emailOrUser)))
            login_emailOrUser.click()

            print(f"[+] Luồng {self.index}: Đã tìm thấy nút Login!")
            
            # Ví dụ: Click vào nút sau khi tìm thấy
            # login_btn.click()
            
            return True
        except Exception as e:
            print(f"[!] Luồng {self.index}: Quá thời gian chờ hoặc không tìm thấy nút Login.")
        return False

    def human_type(self, element, text):
        """Hàm bổ trợ để nhập văn bản từng ký tự một"""
        for char in text:
            element.send_keys(char)
            # Độ trễ ngẫu nhiên giữa các phím từ 0.05 đến 0.25 giây
            time.sleep(random.uniform(0.05, 0.25))

    def login(self):
        
        self.wait_for_login_button()


        time.sleep(5)

        username_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        username_input.clear() # Xóa nội dung cũ nếu có
        self.human_type(username_input, self.username)

        time.sleep(random.uniform(0.5, 1.2))

        password_xpath = '//*[@id="loginContainer"]/div[2]/div/div/form/div[2]/div/div/input'
        password_input = self.driver.find_element(By.XPATH, password_xpath)
        
        password_input.clear()
        self.human_type(password_input, self.password)

        # 3. Nghỉ trước khi ấn Enter hoặc Click Login
        time.sleep(random.uniform(0.8, 1.5))


        self.driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div[2]/div/div/form/div[4]/button').click()

        time.sleep(100)

        self.driver.close()

    def extract_id(self, url):
        # Tìm ID nằm sau 'video/' hoặc 'photo/'
        match = re.search(r'/(?:video|photo)/(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    def like_video(self, max_likes=2):
        count = 0

        while count < max_likes:
            # 1. Giả lập hành vi xem video (Chờ 5-15 giây tùy video)
            watch_time = random.uniform(3, 5) 
            log_info(f"[{self.username}] Đang xem video {watch_time:.1f} giây...")
            time.sleep(watch_time)

            # 2. Thực hiện nhấn Like
            actions = ActionChains(self.driver)
            actions.send_keys("l").perform()
            log_info(f"[{self.username}] Đã nhấn Like lần {count + 1}")
            
            # 3. Chờ một chút sau khi Like để hệ thống ghi nhận (QUAN TRỌNG)
            time.sleep(random.uniform(2, 4)) 

            # 4. Nhấn mũi tên xuống để sang video tiếp theo
            actions.send_keys(Keys.ARROW_DOWN).perform()
            count += 1
            
            time.sleep(random.uniform(3, 5))

        actions.send_keys(Keys.ARROW_DOWN).perform()

    def wait_for_captcha(self):
        # Thay XPATH bên dưới bằng XPATH của khung Captcha/Vòng xoay/Thông báo Captcha
        captcha_xpath = '//*[@class="captcha-container"]' # Ví dụ
        
        try:
            # Kiểm tra xem Captcha có xuất hiện không (đợi thử 3 giây)
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, captcha_xpath))
            )
            log_info(f"[{self.username}] ⚠️ Phát hiện Captcha! Đang đợi giải...")
            
            # Vòng lặp đợi cho đến khi Captcha biến mất hoàn toàn
            while True:
                captchas = self.driver.find_elements(By.XPATH, captcha_xpath)
                if len(captchas) == 0:
                    log_info(f"[{self.username}] ✅ Captcha đã được giải, tiếp tục công việc.")
                    break
                time.sleep(2) # Mỗi 2 giây kiểm tra lại 1 lần
        except:
            # Nếu sau 3 giây không thấy Captcha thì coi như không có, chạy tiếp
            pass

    def extract_video_id(self, url):
        """Trích xuất ID video/photo từ URL bằng Regex linh hoạt"""
        if not url: return None
        match = re.search(r'/(?:video|photo|v)/(\d+)', url)
        if match: return match.group(1)
        
        parts = url.split('?')[0].split('/')
        for part in reversed(parts):
            if part.isdigit() and len(part) > 10:
                return part
        return None

    def click_user_search_result(self, username):
        """
        Click vào avatar của người dùng đầu tiên trong kết quả tìm kiếm
        Dựa trên cấu hình HTML bạn cung cấp.
        """
        try:
            log_info(f"👆 [{self.username}] Đang tìm click avatar của @{username}...")
            
            # Tìm container chứa avatar (dựa trên class bạn gửi)
            # Ưu tiên tìm img có class user-avatar nằm trong div tìm kiếm
            avatar_xpath = f'//div[contains(@class, "user-avatar-container")]//img[contains(@alt, "{username}")] | //div[contains(@class, "user-avatar-container")]//img'
            
            avatar_img = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, avatar_xpath))
            )
            
            # Sử dụng ActionChains để click chính xác vào tâm ảnh
            actions = ActionChains(self.driver)
            actions.move_to_element(avatar_img).pause(random.uniform(0.5, 1.0)).click().perform()
            
            log_info(f"✅ [{self.username}] Đã click vào Avatar người dùng.")
            time.sleep(3) # Đợi trang cá nhân load
            return True
        except Exception as e:
            log_error(f"❌ [{self.username}] Không click được avatar: {str(e)}")
            # Nếu search item không click được avatar, thử click vào text username
            try:
                username_text = self.driver.find_element(By.XPATH, f'//p[text()="{username}"]')
                username_text.click()
                return True
            except:
                return False
            
    def search_username(self, link):
        """Tìm kiếm username và nhấn Enter với cơ chế xử lý lỗi mới"""
        usernameJob = self.resolve_username(link)
        if not usernameJob: return False

        log_info(f"🔍 [{self.username}] Bắt đầu tìm kiếm profile: {usernameJob}")

        try:
            filter_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="app"]/div[2]/div/div/div[2]/div[2]/button/div/div[1]/div')
                )
            )

            filter_btn.click()
            input_box = self.driver.find_element(
                By.XPATH,
                '//*[@id="app"]/div[2]/div/div/div[5]/div[1]/div[2]/form/input'
            )
            log_info(f"🚀 [{self.username}] Đã gửi yêu cầu tìm kiếm cho {usernameJob}")
            time.sleep(1)
            for char in usernameJob:
                input_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))

            input_box.send_keys(Keys.ENTER)


            # Chờ trang kết quả tải xong
            time.sleep(random.uniform(3, 5))
            return usernameJob

        except Exception as e:
            log_error(f"❌ [{self.username}] Lỗi tại search_username")
            # Backup: Thử truy cập trực tiếp bằng URL nếu search lỗi
            log_info(f"🔄 [{self.username}] Thử phương án dự phòng: Truy cập URL trực tiếp")
            self.driver.get(f"https://www.tiktok.com/search/user?q={usernameJob}")
            time.sleep(4)
            return usernameJob

    def click_first_video(self, username):
        """Truy cập profile và click video đầu tiên (Bỏ qua video đang LIVE)"""
        try:
            if f"@{username}" not in self.driver.current_url:
                if not self.click_user_search_result(username):
                    log_info(f"🔄 [{self.username}] Thử truy cập trực tiếp URL profile")
                    self.driver.get(f'https://www.tiktok.com/@{username}')
            
            time.sleep(4)

            # XPATH cải tiến: 
            # 1. Tìm các thẻ a chứa video
            # 2. Loại bỏ các phần tử có chứa text 'LIVE' hoặc các class đặc trưng của Live stream
            video_xpath = (
                '//div[@data-e2e="user-post-item-list"]//div[not(contains(., "LIVE")) and not(contains(., "Live"))]//a | '
                '//div[contains(@id, "grid-item-container-0")]//a[not(contains(., "LIVE"))]'
            )

            # Đợi cho đến khi ít nhất một video không phải LIVE xuất hiện
            videos = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, video_xpath))
            )

            if not videos:
                log_error(f"❌ [{self.username}] Không tìm thấy video hợp lệ (có thể toàn bộ là LIVE)")
                return False

            first_valid_video = videos[0]
            
            # Di chuyển chuột tới rồi mới click
            actions = ActionChains(self.driver)
            actions.move_to_element(first_valid_video).pause(1.5).click().perform()
            
            log_info(f"✅ [{self.username}] Đã mở video đầu tiên (Đã né LIVE)")
            return True
        except Exception as e:
            log_error(f"❌ [{self.username}] Lỗi click video: {str(e)}")
            return False

    def like_video_job(self, job):
        """Thực hiện Like với cơ chế chống nhả Like"""
        link = job.get("full_link")
        expected_video_id = self.extract_video_id(link)
        
        if not expected_video_id:
            log_warning(f"❌ [{self.username}] ID mục tiêu không hợp lệ")
            return False

        log_info(f"🚀 [{self.username}] Bắt đầu Like ID: {expected_video_id}")
        
        try:            
            max_retry = 10
            retry = 0
            is_liked = False

            while retry < max_retry:
                time.sleep(random.uniform(3, 5))
                current_url = self.driver.current_url
                current_video_id = self.extract_video_id(current_url)

                if current_video_id == expected_video_id:
                    log_info(f"✅ [{self.username}] Khớp ID. Đang xem giả lập...")
                    
                    time.sleep(random.uniform(3, 5))

                    try:
                        # Xpath tìm svg/div của nút Like
                        like_btn = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//button[@data-e2e="browse-like-icon"] | //span[@data-e2e="like-icon"]'))
                        )
                        
                        # Kiểm tra xem đã Like chưa (tránh nhấn nhầm thành Unlike)
                        is_already_liked = self.driver.execute_script("""
                            let btn = arguments[0];
                            let svg = btn.querySelector('svg');
                            return svg ? (window.getComputedStyle(svg).fill.includes('rgb(255, 60, 83)') || svg.getAttribute('fill') === '#ff3c53') : false;
                        """, like_btn)

                        if is_already_liked:
                            log_info(f"⚠️ [{self.username}] Video này đã được Like trước đó.")
                            is_liked = True
                            break

                        # 3. Thao tác Like "Người thật": Move -> Pause -> Click
                        actions = ActionChains(self.driver)
                        actions.move_to_element(like_btn).pause(random.uniform(0.5, 1.2)).click().perform()
                        
                        log_info(f"❤️ [{self.username}] Đã nhấn Like bằng Click chuột!")
                        
                    except Exception as e:
                        log_warning(f"⚠️ [{self.username}] Không click được nút Like, dùng phím tắt L...")
                        actions = ActionChains(self.driver)
                        actions.send_keys("l").perform()

                    # 4. QUAN TRỌNG: Xem tiếp sau khi Like để "chốt" dữ liệu
                    time.sleep(random.uniform(5, 7))
                    is_liked = True
                    break
                else:
                    log_warning(f"🔄 [{self.username}] Đang ở ID {current_video_id}, cuộn xuống tìm...")
                    actions = ActionChains(self.driver)
                    actions.send_keys(Keys.ARROW_DOWN).perform()
                    retry += 1

            if is_liked:
                log_info(f"✨ [{self.username}] Hoàn thành Like thành công!")
                return True
            
            self.driver.get('https://www.tiktok.com/')
            return False

        except Exception as e:
            log_error(f"⚠️ [{self.username}] Lỗi Like: {str(e)}")
            return False 
    
    def start(self, job):
        link = job.get("full_link")

        username_found = self.search_username(link)
        if not username_found:
            log_warning("❌ Không lấy được username → next job")
            return False

        
        time.sleep(2)

        if not self.click_first_video(username_found):
            return False

        time.sleep(1)
        if not self.like_video_job(job):
            return False
        
        time.sleep(5)

        self.driver.get('https://www.tiktok.com/')

        return True

    def restart(self):
        try:
            self.driver.quit()
        except:
            pass
        self._create_driver()

    def close(self):
        if self.driver:
            self.driver.quit()

    def wait_for_register_button(self, timeout=20):
        try:
            print(f"[*] Luồng {self.index}: Đang đợi nút Login xuất hiện...")
            
            # Thiết lập đợi tối đa 'timeout' giây
            wait = WebDriverWait(self.driver, timeout)
            
            # Đợi cho đến khi phần tử hiện diện và có thể click được
            xpath_login = '//*[@id="top-right-action-bar-login-button"]/div/div'
            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_login)))
            login_btn.click()

            time.sleep(1)

            xpath_login_span = '//*[@id="loginModalContentContainer"]/div[3]/a/span'
            xpath_login_span = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_login_span)))
            xpath_login_span.click()

            #
            xpath_regisUser = '//*[@id="loginContainer"]/div[1]/div/div/div[2]/div/div/div[1]/div[2]/div[2]/div'
            xpath_regisUser = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_regisUser)))
            xpath_regisUser.click()
            
            time.sleep(1)
            #
            xpath_emailOrUser = '//*[@id="loginContainer"]/div[2]/div/form/div[4]/span[2]/a'
            login_emailOrUser = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_emailOrUser)))
            login_emailOrUser.click()

            print(f"[+] Luồng {self.index}: Đã tìm thấy nút Login!")
            
            # Ví dụ: Click vào nút sau khi tìm thấy
            # login_btn.click()
            
            return True
        except Exception as e:
            print(f"[!] Luồng {self.index}: Quá thời gian chờ hoặc không tìm thấy nút Login.")
        return False

    def random_month(self):
        random_month = random.randint(1, 12)

        # Click dropdown tháng
        month_dropdown = self.driver.find_element(
            By.XPATH, '//*[@id="loginContainer"]/div[2]/div/form/div[2]/div[1]'
        )
        month_dropdown.click()
        time.sleep(0.5)

        month_option_xpath = f"//*[contains(@id, 'Month-options-item-{random_month-1}')]"

        found = False

        for _ in range(5):  # thử tối đa 5 lần
            try:
                month_option = self.driver.find_element(By.XPATH, month_option_xpath)
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", month_option)
                time.sleep(0.3)
                month_option.click()
                found = True
                break
            except NoSuchElementException:
                # Scroll xuống nếu chưa thấy
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(0.5)

        if found:
            log_info(f"✅ Đã chọn ngẫu nhiên tháng: {random_month}")
        else:
            log_error("❌ Không tìm thấy option tháng sau khi scroll")

    def random_day(self):
        random_day = random.randint(1, 28)  # 1-28 cho an toàn mọi tháng

        # 1️⃣ Click dropdown Day
        day_dropdown = self.driver.find_element(
            By.XPATH,
            '//*[@id="loginContainer"]/div[2]/div/form/div[2]/div[2]'
        )
        day_dropdown.click()
        time.sleep(0.5)

        day_option_xpath = f"//*[contains(@id, 'Day-options-item-{random_day-1}')]"

        found = False

        for _ in range(5):  # thử tối đa 5 lần
            try:
                day_option = self.driver.find_element(By.XPATH, day_option_xpath)

                # Scroll tới phần tử (tránh bị che)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    day_option
                )
                time.sleep(0.3)

                day_option.click()
                found = True
                break

            except NoSuchElementException:
                # Scroll dropdown xuống nếu chưa thấy
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(0.5)

        if found:
            log_info(f"✅ Đã chọn ngẫu nhiên ngày: {random_day}")
        else:
            log_error("❌ Không tìm thấy option Day sau khi scroll")

    def random_year(self):
        # Ví dụ chọn năm từ 1990 -> 2004 (18+)
        random_year = random.randint(1990, 2004)

        # 1️⃣ Click dropdown Year
        year_dropdown = self.driver.find_element(
            By.XPATH,
            '//*[@id="loginContainer"]/div[2]/div/form/div[2]/div[3]'
        )
        year_dropdown.click()
        time.sleep(0.5)

        # Nếu ID dạng Year-options-item-INDEX (0-based)
        # Thường index = năm - năm bắt đầu
        # Nếu list bắt đầu từ 2005 thì cần chỉnh lại
        year_index = random_year - 1900  # ⚠️ chỉnh lại nếu cần
        year_option_xpath = f"//*[contains(@id, 'Year-options-item-{year_index}')]"

        found = False

        for _ in range(6):
            try:
                year_option = self.driver.find_element(By.XPATH, year_option_xpath)

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    year_option
                )
                time.sleep(0.3)

                year_option.click()
                found = True
                break

            except NoSuchElementException:
                # Scroll xuống
                self.driver.execute_script("window.scrollBy(0, 400);")
                time.sleep(0.5)

        if found:
            log_info(f"✅ Đã chọn năm: {random_year}")
        else:
            log_error("❌ Không tìm thấy option Year")

    def input_email(self, email):
        wait = WebDriverWait(self.driver, 10)

        email_input = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//*[@id="loginContainer"]/div[2]/div/form/div[5]/div/div/input'
            ))
        )

        email_input.clear()

        # Gõ từng ký tự cho tự nhiên hơn
        for char in email:
            email_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        log_info(f"✅ Đã nhập email: {email}")

    def input_password(self, password):
        try:
            password_input = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//*[@id="loginContainer"]/div[2]/div/form/div[6]/div/div/input'
                ))
            )

            password_input.clear()
            password_input.send_keys(password)

        except Exception as e:
            print("❌ Không nhập được password:", e)

    def click_get_otp(self):
        try:
            btn = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//*[@id="loginContainer"]/div[2]/div/form/div[7]/div/div/button'
                ))
            )
            btn.click()
            print("✅ Đã click Get OTP")

        except Exception as e:
            print("❌ Không click được Get OTP:", e)

    def wait_for_otp(self, email, timeout=120):
        url = "https://checkotpmail.com/api/check-stream"

        headers = {
            "Referer": "https://checkotpmail.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json={"emails": [email]},
                    timeout=20
                )

                data = response.json()

                # Nếu trả dạng list
                if isinstance(data, list) and len(data) > 0:
                    code = data[0].get("code")

                # Nếu trả dạng dict
                else:
                    code = data.get("code")

                if code and code != "Không có OTP":
                    print("✅ OTP nhận được:", code)
                    return code

                print("⏳ Chưa có OTP...")

            except Exception as e:
                print("⚠ Lỗi check OTP:", e)

            time.sleep(5)

        print("❌ Hết thời gian chờ OTP")
        return None

    def register(self):

        #mua email
        shopMail = Shop1989ND('dungadeptry', 'Dungg2005@')
        result = shopMail.buy_resource(product_id=5, amount=1)
        accounts = shopMail.extract_email_pass(result)

        if result.get("status") != "success":
            print("❌ Mua mail thất bại:", result)
            return

        if not accounts:
            log_error("❌ Không có mail trả về")
            return
        
        self.wait_for_register_button(20)

        time.sleep(3)
        self.random_month()

        time.sleep(2)
        self.random_day()

        time.sleep(2)
        self.random_year()

        # Lấy mail đầu tiên
        email_pass = accounts[0]
        email, password = email_pass.split("|")
        log_info(f"📩 Mail mua được: {email}")
        # nhập email vào form
        self.input_email(email)
        # nếu cần lưu password để dùng sau
        self.email_password = password
        self.input_password("Sieunhanga12@")

        self.click_get_otp()

        otp = self.wait_for_otp(email, timeout=60)

        if otp:
            self.input_otp(otp)
        else:
            print("❌ Không lấy được OTP")

