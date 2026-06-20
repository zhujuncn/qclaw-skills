#!/usr/bin/env python3
"""
Wizz Air 航班查询 - v5.0 分批防检测版
===========================================
优化策略：
1. 分批查询 - 每批N个目的地，批次间暂停M分钟
2. 动态延迟 - 随机2-5秒，随查询次数递增
3. 会话保持 - 检测异常时保存进度，可断点续查
4. 智能暂停 - 连续N次异常后暂停
5. 用户代理轮换 - 模拟真实用户
"""

import asyncio
import os
import re
import random
import json
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import pandas as pd

# ============================================================================
# 🔧 配置区
# ============================================================================

EMAIL = "stuartdzhu@gmail.com"
PASSWORD = "suzhou2021"
SUB_URL = "https://multipass.wizzair.com/en/w6/subscriptions/availability/69571f34-aeea-44ca-ba8e-4fcb13b6a8c8"

OUTPUT_DIR = "wizz_air_results"
HEADLESS_MODE = False
PROGRESS_FILE = "wizz_air_results/progress.json"

# ===== 防检测配置 =====
BATCH_SIZE = 15          # 每批查询目的地数量
BATCH_PAUSE_MIN = 180    # 批次间暂停时间（秒）= 3分钟
MIN_DELAY = 2.0          # 最小延迟（秒）
MAX_DELAY = 5.0          # 最大延迟（秒）
DELAY_INCREMENT = 0.1    # 延迟递增值（每10次查询）
CONSECUTIVE_ERROR_LIMIT = 5  # 连续异常阈值
ERROR_PAUSE_TIME = 60    # 异常后暂停时间（秒）

# 用户代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# ============================================================================
# 辅助函数
# ============================================================================

def save_progress(origin_code, completed_dests, all_results):
    """保存进度"""
    progress = {
        "origin_code": origin_code,
        "completed_dests": completed_dests,
        "timestamp": datetime.now().isoformat(),
        "results_count": len(all_results)
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)
    print(f"💾 进度已保存: {len(completed_dests)} 个目的地已完成", flush=True)

def load_progress():
    """加载进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return None

def extract_flights(body: str):
    """提取航班信息"""
    flights = []
    pattern = r'(\d{2}:\d{2})\s*(?:UTC[^\n]*\n[^\n]+)\s*([\dh\sm]+)\s*(\d{2}:\d{2})\s*(?:UTC[^\n]*\n[^\n]+)'
    matches = re.findall(pattern, body)
    for m in matches:
        flights.append({
            "departure": m[0],
            "arrival": m[2],
            "duration": m[1].strip()
        })
    return flights

def get_user_input():
    """获取用户输入"""
    print("\n" + "=" * 70, flush=True)
    print("  WIZZ AIR 航班查询 - v5.0 分批防检测版", flush=True)
    print("=" * 70, flush=True)
    
    print("\n📍 出发城市配置", flush=True)
    print("-" * 70, flush=True)
    print("常用城市代码：", flush=True)
    print("  OTP - Bucharest | WAW - Warsaw | BEG - Belgrade | TLL - Tallinn", flush=True)
    print("  IAS - Iasi | VNO - Vilnius | KRK - Kraków | GHV - Gävle", flush=True)
    
    origin_code = input("\n请输入出发城市代码: ").strip().upper()
    origin_name = input("请输入出发城市名称: ").strip()
    
    if not origin_code:
        origin_code = "OTP"
        origin_name = "Bucharest"
    
    print("\n📅 日期配置", flush=True)
    print("-" * 70, flush=True)
    print("  1 - 查询未来 N 天")
    print("  2 - 指定具体日期")
    
    mode = input("请选择 (1 或 2): ").strip()
    
    if mode == "2":
        dates_str = input("请输入日期 (YYYY-MM-DD，多个用空格分隔): ").strip()
        dates = dates_str.split()
        try:
            dates = [datetime.strptime(d, "%Y-%m-%d").strftime("%d-%m-%Y") for d in dates]
        except:
            print("日期格式错误，使用默认4天")
            today = datetime.now()
            dates = [(today + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(4)]
    else:
        days = input("请输入查询天数（默认 4）: ").strip()
        days = int(days) if days.isdigit() else 4
        today = datetime.now()
        dates = [(today + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(days)]
    
    # 询问批次大小
    batch_input = input(f"\n每批查询目的地数量（默认 {BATCH_SIZE}）: ").strip()
    batch_size = int(batch_input) if batch_input.isdigit() else BATCH_SIZE
    
    print("\n" + "=" * 70, flush=True)
    print(f"  📋 配置确认", flush=True)
    print("=" * 70, flush=True)
    print(f"  出发城市: {origin_code} ({origin_name})", flush=True)
    print(f"  查询日期: {', '.join(dates)}", flush=True)
    print(f"  批次大小: {batch_size} 个目的地/批", flush=True)
    print(f"  批次暂停: {BATCH_PAUSE_MIN} 秒", flush=True)
    print("=" * 70, flush=True)
    
    confirm = input("\n✅ 确认开始查询？(y/n): ").strip().lower()
    if confirm not in ['y', 'yes', '是']:
        print("❌ 已取消", flush=True)
        return None, None, None, batch_size
    
    return origin_code, origin_name, dates, batch_size

# ============================================================================
# 核心函数
# ============================================================================

async def smart_delay(query_count):
    """智能延迟 - 随查询次数递增"""
    base_delay = random.uniform(MIN_DELAY, MAX_DELAY)
    increment = (query_count // 10) * DELAY_INCREMENT
    delay = base_delay + increment
    await asyncio.sleep(delay)

async def check_security(page) -> bool:
    """检测安全检查"""
    try:
        body = await page.inner_text("body")
        return "Security check" in body or "security check" in body.lower()
    except:
        return False

async def handle_security_check(page):
    """处理安全检查 - 新策略：等待用户手动处理"""
    print("\n⚠️ 检测到安全检查！", flush=True)
    print("请手动完成验证（如果需要），等待 60 秒后继续...", flush=True)
    await asyncio.sleep(60)
    
    # 不刷新页面，直接继续
    try:
        # 检查是否还在安全页面
        body = await page.inner_text("body")
        if "Security check" in body:
            print("❌ 仍在安全检查页面，请手动处理", flush=True)
            return False
        return True
    except:
        return False

async def get_available_destinations(page):
    """获取可用目的地"""
    print("\n📍 获取可用目的地列表...", flush=True)
    
    dest_input = page.locator('input[id^="autocomplete-destination"]')
    lists = page.locator('ul.autocomplete-result-list')
    
    await dest_input.click()
    await asyncio.sleep(2)
    
    destinations = []
    
    for i in range(await lists.count()):
        items = lists.nth(i).locator('li')
        count = await items.count()
        
        for j in range(count):
            try:
                item = items.nth(j)
                if await item.is_visible():
                    text = await item.inner_text()
                    destinations.append(text.strip())
            except:
                pass
    
    # 解析目的地
    parsed_dests = []
    for dest in destinations:
        if dest and len(dest) > 0:
            match = re.search(r'\(([A-Z]{3})\)', dest)
            if match:
                code = match.group(1)
                # 提取城市名
                name_match = re.match(r'^([^(]+)', dest)
                name = name_match.group(1).strip() if name_match else code
                parsed_dests.append((code, name))
    
    print(f"✅ 找到 {len(parsed_dests)} 个可用目的地", flush=True)
    return parsed_dests

async def select_destination(page, dest_code):
    """选择目的地"""
    try:
        dest_input = page.locator('input[id^="autocomplete-destination"]')
        lists = page.locator('ul.autocomplete-result-list')
        
        await dest_input.click()
        await asyncio.sleep(0.2)
        await dest_input.fill(dest_code)
        await asyncio.sleep(1.5)
        
        found = False
        for i in range(await lists.count()):
            items = lists.nth(i).locator('li')
            count = await items.count()
            
            for j in range(count):
                try:
                    item = items.nth(j)
                    if await item.is_visible():
                        text = await item.inner_text()
                        if dest_code in text:
                            await item.click()
                            found = True
                            break
                except:
                    continue
            if found:
                break
        
        return found
    except:
        return False

async def query_flight(page, dest_code, date_str, query_count):
    """查询单个航班"""
    try:
        date_input = page.locator('#Departure-date')
        btn = page.locator('button:has-text("SEARCH")')
        
        await date_input.click()
        await asyncio.sleep(0.2)
        await date_input.fill(date_str)
        await asyncio.sleep(0.5)
        await date_input.press("Escape")
        await asyncio.sleep(0.5)
        
        # 检查按钮状态
        if not await btn.is_enabled():
            # 触发 dirty
            await date_input.click()
            await date_input.fill(date_str + " ")
            await asyncio.sleep(0.3)
            await date_input.fill(date_str)
            await asyncio.sleep(0.3)
            await date_input.press("Escape")
            await asyncio.sleep(0.3)
        
        if not await btn.is_enabled():
            return "❌ 按钮禁用", []
        
        await btn.click()
        await asyncio.sleep(4)
        
        body = await page.inner_text("body")
        
        if "Sorry, no results were found" in body:
            return "✗ 无票", []
        elif "Your first All You Can Fly flight" in body:
            flights = extract_flights(body)
            return "✓ 有票", flights
        else:
            return "❌ 未知页面", []
    
    except Exception as e:
        return f"❌ {str(e)[:30]}", []

# ============================================================================
# 主函数
# ============================================================================

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 获取用户输入
    origin_code, origin_name, dates, batch_size = get_user_input()
    
    if origin_code is None:
        return
    
    # 检查是否有保存的进度
    progress = load_progress()
    completed_dests = set()
    
    if progress and progress.get("origin_code") == origin_code:
        print(f"\n🔄 发现保存的进度: {len(progress['completed_dests'])} 个目的地已完成", flush=True)
        resume = input("是否继续上次查询？(y/n): ").strip().lower()
        if resume in ['y', 'yes', '是']:
            completed_dests = set(progress['completed_dests'])
            print(f"✅ 将跳过 {len(completed_dests)} 个已完成的目的地", flush=True)
    
    all_results = []
    query_count = 0
    consecutive_errors = 0
    
    async with async_playwright() as p:
        # 随机用户代理
        user_agent = random.choice(USER_AGENTS)
        browser = await p.chromium.launch(headless=HEADLESS_MODE)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()
        page.set_default_timeout(45000)
        
        print(f"\n🔐 登录... (UA: {user_agent[:50]}...)", flush=True)
        try:
            await page.goto("https://multipass.wizzair.com", wait_until="domcontentloaded", timeout=30000)
        except:
            await page.goto("https://multipass.wizzair.com", wait_until="commit", timeout=30000)
        await asyncio.sleep(5)
        
        try:
            await page.click('button:has-text("SIGN IN")', timeout=15000)
            await asyncio.sleep(2)
            await page.fill('input[placeholder="e-mail"]', EMAIL, timeout=10000)
            await page.fill('input[placeholder="Password"]', PASSWORD, timeout=10000)
            await page.click('input[type="submit"]', timeout=60000)
            await asyncio.sleep(5)
            print("✅ 登录完成", flush=True)
        except:
            print("⚠️ 登录遇到问题，继续...", flush=True)
        
        await page.goto(SUB_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(8)
        
        # 关闭可能出现的 WalletModal 弹窗
        try:
            close_btn = page.locator('.WalletModal button, .WalletModal button.close, .vm--close, .CvoModal-content button')
            if await close_btn.count() > 0:
                await close_btn.first.click()
                await asyncio.sleep(2)
                print("✅ 弹窗已关闭", flush=True)
        except:
            pass
        
        # 选择出发地
        origin_input = page.locator('input[id^="autocomplete-origin"]')
        lists = page.locator('ul.autocomplete-result-list')
        
        try:
            await origin_input.wait_for(state="visible", timeout=10000)
        except:
            await asyncio.sleep(5)
        
        origin_value = await origin_input.input_value(timeout=10000)
        print(f"\n当前出发地: {origin_value}", flush=True)
        
        if origin_code not in origin_value:
            print(f"选择出发地 {origin_code}...", flush=True)
            await origin_input.click()
            await asyncio.sleep(0.2)
            await origin_input.fill(origin_code)
            await asyncio.sleep(2)
            
            found_origin = False
            for i in range(await lists.count()):
                items = lists.nth(i).locator('li')
                for j in range(await items.count()):
                    try:
                        item = items.nth(j)
                        if await item.is_visible():
                            text = await item.inner_text()
                            if origin_code in text:
                                await item.click()
                                found_origin = True
                                break
                    except:
                        continue
                if found_origin:
                    break
            
            await asyncio.sleep(1)
            print("✅ 出发地已选择", flush=True)
        
        # 获取目的地
        dests = await get_available_destinations(page)
        
        if not dests:
            print("❌ 没有可用目的地", flush=True)
            await browser.close()
            return
        
        print("\n📋 目的地列表:", flush=True)
        for code, city in dests:
            status = "✓" if code in completed_dests else " "
            print(f"  [{status}] {code} ({city})", flush=True)
        print()
        
        # 过滤已完成的目的地
        pending_dests = [(c, n) for c, n in dests if c not in completed_dests]
        print(f"待查询: {len(pending_dests)} 个目的地", flush=True)
        
        # 重新选择出发地
        await origin_input.click()
        await asyncio.sleep(0.2)
        await origin_input.fill(origin_code)
        await asyncio.sleep(2)
        
        for i in range(await lists.count()):
            items = lists.nth(i).locator('li')
            for j in range(await items.count()):
                try:
                    item = items.nth(j)
                    if await item.is_visible():
                        text = await item.inner_text()
                        if origin_code in text:
                            await item.click()
                            break
                except:
                    continue
        
        await asyncio.sleep(1)
        print("✅ 出发地已确认\n", flush=True)
        
        # ===== 分批查询 =====
        total = len(pending_dests) * len(dates)
        start_time = datetime.now()
        batch_num = 0
        
        for batch_start in range(0, len(pending_dests), batch_size):
            batch = pending_dests[batch_start:batch_start + batch_size]
            batch_num += 1
            
            print(f"\n{'='*70}", flush=True)
            print(f"  📦 批次 {batch_num} - 目的地 {batch_start+1}-{batch_start+len(batch)}/{len(pending_dests)}", flush=True)
            print(f"{'='*70}", flush=True)
            
            for dest_idx, (dest_code, dest_name) in enumerate(batch):
                # 检查安全
                if await check_security(page):
                    success = await handle_security_check(page)
                    if not success:
                        print("❌ 安全检查未通过，保存进度并退出", flush=True)
                        save_progress(origin_code, list(completed_dests), all_results)
                        await browser.close()
                        return
                
                print(f"\n3️⃣ 选择目的地 {dest_code} ({dest_name})...", flush=True)
                found_dest = await select_destination(page, dest_code)
                
                if not found_dest:
                    print(f"❌ 无法选择，跳过", flush=True)
                    for date in dates:
                        query_count += 1
                        all_results.append({
                            "出发地": f"{origin_code} - {origin_name}",
                            "目的地": f"{dest_code} - {dest_name}",
                            "日期": date,
                            "状态": "❌ 未找到",
                            "出发时间": "",
                            "到达时间": "",
                            "飞行时长": "",
                        })
                    completed_dests.add(dest_code)
                    continue
                
                await asyncio.sleep(1)
                print(f"✅ 已选择\n", flush=True)
                
                print(f"4️⃣ 查询 {dest_code} 的 {len(dates)} 个日期:", flush=True)
                
                for date in dates:
                    query_count += 1
                    await smart_delay(query_count)
                    
                    status, flights = await query_flight(page, dest_code, date, query_count)
                    
                    # 计算进度
                    current = sum(1 for _ in range(batch_start)) * len(dates) + dest_idx * len(dates) + dates.index(date) + 1
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    eta = elapsed / current * (total - current) if current > 0 else 0
                    
                    flight_info = ""
                    if flights:
                        flight_info = f"{flights[0]['departure']}→{flights[0]['arrival']}"
                        for f in flights:
                            all_results.append({
                                "出发地": f"{origin_code} - {origin_name}",
                                "目的地": f"{dest_code} - {dest_name}",
                                "日期": date,
                                "状态": status,
                                "出发时间": f["departure"],
                                "到达时间": f["arrival"],
                                "飞行时长": f["duration"],
                            })
                    else:
                        all_results.append({
                            "出发地": f"{origin_code} - {origin_name}",
                            "目的地": f"{dest_code} - {dest_name}",
                            "日期": date,
                            "状态": status,
                            "出发时间": "",
                            "到达时间": "",
                            "飞行时长": "",
                        })
                    
                    print(f"  [{current:3d}/{total}] {date}  {status} {flight_info}  ETA:{int(eta)}min", flush=True)
                    
                    # 检查连续错误
                    if "❌" in status:
                        consecutive_errors += 1
                        if consecutive_errors >= CONSECUTIVE_ERROR_LIMIT:
                            print(f"\n⚠️ 连续 {consecutive_errors} 次异常，暂停 {ERROR_PAUSE_TIME} 秒...", flush=True)
                            await asyncio.sleep(ERROR_PAUSE_TIME)
                            consecutive_errors = 0
                    else:
                        consecutive_errors = 0
                
                completed_dests.add(dest_code)
            
            # 批次结束，保存进度
            save_progress(origin_code, list(completed_dests), all_results)
            
            # 如果还有下一批，暂停
            if batch_start + batch_size < len(pending_dests):
                print(f"\n⏸️ 批次完成，暂停 {BATCH_PAUSE_MIN} 秒后继续下一批...", flush=True)
                await asyncio.sleep(BATCH_PAUSE_MIN)
        
        await browser.close()
    
    # 生成报告
    if all_results:
        df = pd.DataFrame(all_results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = f"{OUTPUT_DIR}/{origin_code}_flights_{timestamp}.xlsx"
        
        has_ticket = df[df['状态'].str.contains('✓ 有票', na=False)]
        no_ticket = df[df['状态'] == '✗ 无票']
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='全部', index=False)
            if not has_ticket.empty:
                has_ticket.to_excel(writer, sheet_name='有票', index=False)
            if not no_ticket.empty:
                no_ticket.to_excel(writer, sheet_name='无票', index=False)
        
        elapsed = (datetime.now() - start_time).total_seconds() / 60
        
        print(f"\n{'='*70}", flush=True)
        print(f"✅ 完成! 耗时 {elapsed:.1f} 分钟", flush=True)
        print(f"✓ 有票: {len(has_ticket)}", flush=True)
        print(f"✗ 无票: {len(no_ticket)}", flush=True)
        print(f"📊 Excel: {excel_file}", flush=True)
        print(f"{'='*70}", flush=True)
        
        if not has_ticket.empty:
            print(f"\n🎫 有票详情:", flush=True)
            for _, r in has_ticket.iterrows():
                print(f"  {r['目的地']:20s} {r['日期']}  {r['出发时间']}→{r['到达时间']} ({r['飞行时长']})", flush=True)
        
        # 清理进度文件
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        
        # 打开 Excel
        os.system(f"open {excel_file}")

if __name__ == "__main__":
    asyncio.run(main())
