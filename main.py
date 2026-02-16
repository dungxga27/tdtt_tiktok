import threading
import time
import random
import os
import json
import re
from config import DELAY
from core.traodoituongtac import TraoDoiTuongTac
from utils.logger import log_info, log_error, log_warning
from core.selenium_resolver import TikTokResolver
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
# Khóa điều phối trung tâm
job_lock = threading.Lock()

def show_menu():
    # Tạo bảng
    table = Table(title="💎 TIKTOK AUTO TOOL 2026 💎", title_style="bold magenta")

    table.add_column("Lệnh", justify="center", style="cyan", no_wrap=True)
    table.add_column("Hành động", style="white")
    table.add_column("Mô tả", style="dim")

    table.add_row("reg", "Đăng ký tài khoản", "Tạo tài khoản TikTok mới với Proxy")
    table.add_row("Enter", "Chạy Tool", "Bắt đầu login và thực hiện nhiệm vụ")

    # Hiển thị bảng trong một khung Panel cho đẹp
    console.print(Panel(table, expand=False, border_style="blue"))

def get_job_from_file(target_uid, file_name="job.json"):
    """Lấy job dự phòng từ file JSON theo đúng UID và chuyển link full"""
    if not os.path.exists(file_name):
        return None
    
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            full_data = json.load(f)
        
        jobs_list = full_data.get("data", [])
        if not jobs_list:
            return None
        
        found_index = -1
        for i, job in enumerate(jobs_list):
            if job.get("uid") == target_uid:
                found_index = i
                break
        
        if found_index == -1:
            return None
        
        raw_job = jobs_list.pop(found_index)
        video_id = raw_job.get("link")
        full_tiktok_url = f"https://www.tiktok.com/@/video/{video_id}"
        
        processed_job = {
            "job_id": raw_job.get("_id"),
            "full_link": full_tiktok_url, 
            "action": raw_job.get("action"),
            "uid": raw_job.get("uid")
        }
        
        # Cập nhật lại file
        full_data["data"] = jobs_list
        full_data["recordsTotal"] = len(jobs_list)
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(full_data, f, indent=4)
            
        return processed_job
    except Exception as e:
        log_error(f"Lỗi file job.json: {e}")
        return None

def worker(thread_id, raw_data):
    parts = raw_data.split('|')
    username = parts[0] if len(parts) > 0 else "N/A"
    password = parts[1] if len(parts) > 1 else "N/A"
    proxy = parts[2] if len(parts) > 2 else None

    # Khởi tạo Resolver
    tiktok = TikTokResolver(thread_id, proxy, username, password)
    tdtt = TraoDoiTuongTac(username, "tiktok_like")

    log_info(f"[Thread {thread_id}] Tài khoản {username} đã sẵn sàng.")
    job_done_counter = 0

    while True:
        # 1. Thử giành quyền lấy job (không đợi/blocking=False)
        acquired = job_lock.acquire(blocking=False)

        if acquired:
            try:
                log_info(f"🚀 === [{username}] CHIẾM QUYỀN - ĐANG CHECK JOB ===")
                
                start_time_batch = time.time()
                # Cấu hình UID trước khi lấy job
                if not tdtt.config_uid():
                    log_error(f"[{username}] Config UID thất bại.")
                    # Nếu lỗi config thì thoát để nhường lượt
                else:
                    # Lấy job từ API
                    jobs = None

                    # 1️⃣ Lấy job từ file trước
                    file_job = get_job_from_file(username)
                    if file_job:
                        log_info(f"[{username}] Lấy job từ file trước")
                        jobs = [file_job]

                    # 2️⃣ Nếu file không có thì gọi API
                    if not jobs:
                        log_warning(f"[{username}] File không có job, gọi API...")
                        jobs = tdtt.get_job()

                    if jobs:
                        current_batch_success = 0
                        for job in jobs:
                            job_id = job.get("job_id")
                            log_info(f"🎯 [{username}] Đang thực hiện job: {job_id}")
                            
                            if tiktok.start(job):
                                tdtt.report_job(job_id)
                                job_done_counter += 1
                                current_batch_success += 1
                                log_info(f"✅ [{username}] Thành công. Tổng: {job_done_counter}")
                                
                                # if job_done_counter >= 4:
                                #     tdtt.get_coins()
                                #     job_done_counter = 0
                            else:
                                tdtt.report_job(job_id, is_success=False, note="Lỗi")
                            tiktok.like_video(max_likes=1)

                            time.sleep(random.uniform(5, 8))

                        if current_batch_success > 0:
                            elapsed_time = round(time.time() - start_time_batch, 2)
                            log_info(f"💰 [{username}] Hoàn thành đợt làm job!")
                            log_info(f"⏱️ [{username}] Tổng thời gian thực hiện: {elapsed_time} giây")
                            log_info(f"💵 [{username}] Đang nhận tiền cho {current_batch_success} job...")
                            tdtt.get_coins()
                    else:
                        log_info(f"😴 [{username}] Hết sạch job! Đang nhường lượt...")

            except Exception as e:
                log_error(f"Lỗi luồng {username}: {e}")
            finally:
                # 2. Quan trọng: Nhả khóa
                job_lock.release()
                
                # 3. Ép buộc Nick vừa check xong đi Like dạo để nhường Nick khác chiếm Lock
                log_info(f"📱 [{username}] Nhả ghế -> Chuyển sang lướt TikTok dạo...")
                tiktok.like_video(max_likes=1)
                time.sleep(random.uniform(10, 15)) # Nghỉ đủ lâu để thread khác nhảy vào acquire()
        
        else:
            try:
                tiktok.like_video(max_likes=1)
            except:
                time.sleep(5)

def login(thread_id, raw_data):
    parts = raw_data.split('|')
    username = parts[0] if len(parts) > 0 else "N/A"
    password = parts[1] if len(parts) > 1 else "N/A"
    proxy = parts[2] if len(parts) > 2 else None

    tiktok = TikTokResolver(thread_id, proxy, username, password)
    tiktok.login()

def run():
    print("=" * 50)
    print("   TOOL TIKTOK TDTT - PHIÊN BẢN XOAY VÒNG")
    print("=" * 50)
    
    # 1. Chọn chế độ hoặc nhập file
    show_menu()
    action = console.input("[bold yellow]Nhập lựa chọn của bạn: ").strip().lower()
    
    inp = input("Nhập tên file (mặc định 'accounts.txt'): ").strip()
    file_path = inp if inp else "accounts.txt"

    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        print(f"❌ File trống!")
        return

    # 2. Xử lý chế độ LOGIN thủ công
    if action == "login":
        target_user = input("Nhập Username cần login (phải giống trong file): ").strip()
        found_line = None
        for line in lines:
            if line.startswith(target_user):
                found_line = line
                break
        
        if found_line:
            print(f"🚀 Đang mở trình duyệt cho {target_user} để login...")
            # Chạy login xong thì kết thúc hoặc bạn có thể sửa để chạy tiếp
            login(1, found_line)
            return
        else:
            print(f"❌ Không tìm thấy tài khoản {target_user} trong danh sách!")
            return
    
    if action == "reg":
        # Yêu cầu người dùng nhập key
        proxy = input("Vui lòng nhập proxy: ").strip()
        
        # if not proxy:
        #     print("Lỗi: proxy không được để trống!")
        # else:
            # Giả sử bạn thêm tham số api_key vào cuối TikTokResolver
        tiktok = TikTokResolver(1, proxy)
        tiktok.register()
        return

    # 3. Chế độ chạy TOOL XOAY VÒNG bình thường
    log_info(f"Đang khởi động {len(lines)} luồng tài khoản...")
    threads = []
    for i, line in enumerate(lines, start=1):
        t = threading.Thread(target=worker, args=(i, line))
        t.daemon = True
        t.start()
        threads.append(t)
        time.sleep(3)

    for t in threads:
        t.join()

if __name__ == "__main__":
    run()