#!/usr/bin/env python3
"""
获取 Wizz Air 从指定城市出发的实际可用目的地列表
通过点击 To 下拉菜单获取真实航线
"""

import asyncio
from playwright.async_api import async_playwright

# 配置
EMAIL = "stuartdzhu@gmail.com"
PASSWORD = "suzhou2021"
SUB_URL = "https://multipass.wizzair.com/en/w6/subscriptions/availability/69571f34-aeea-44ca-ba8e-4fcb13b6a8c8"

# 出发地
ORIGIN_CODE = "TLL"
ORIGIN_NAME = "Tallinn"

async def main():
    print("=" * 70)
    print(f"获取 {ORIGIN_CODE} ({ORIGIN_NAME}) 出发的可用目的地")
    print("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # 登录
        print("\n🔐 登录...", flush=True)
        await page.goto("https://multipass.wizzair.com", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)
        await page.click('button:has-text("SIGN IN")', timeout=60000)
        await asyncio.sleep(3)
        await page.fill('input[placeholder="e-mail"]', EMAIL, timeout=10000)
        await page.fill('input[placeholder="Password"]', PASSWORD, timeout=10000)
        await page.click('input[type="submit"]', timeout=60000)
        await asyncio.sleep(5)
        print("✅ 登录完成\n", flush=True)
        
        # 进入搜索页
        await page.goto(SUB_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        
        # 选择出发地
        print(f"1️⃣ 选择出发地 {ORIGIN_CODE}...", flush=True)
        lists = page.locator('ul.autocomplete-result-list')
        origin_input = page.locator('input[id^="autocomplete-origin"]')
        
        await origin_input.click()
        await asyncio.sleep(0.2)
        await origin_input.fill(ORIGIN_CODE)
        await asyncio.sleep(1.5)
        
        found_origin = False
        for i in range(await lists.count()):
            items = lists.nth(i).locator('li')
            for j in range(await items.count()):
                text = await items.nth(j).inner_text()
                if ORIGIN_CODE in text and await items.nth(j).is_visible():
                    await items.nth(j).click()
                    found_origin = True
                    break
            if found_origin:
                break
        
        if not found_origin:
            print(f"❌ 无法选择出发地 {ORIGIN_CODE}", flush=True)
            await browser.close()
            return
        
        await asyncio.sleep(1)
        print(f"✅ 出发地已选择\n", flush=True)
        
        # 点击 To 下拉菜单获取可用目的地
        print("2️⃣ 点击 To 下拉菜单获取可用目的地...", flush=True)
        dest_input = page.locator('input[id^="autocomplete-destination"]')
        
        await dest_input.click()
        await asyncio.sleep(2)  # 等待下拉菜单加载
        
        # 获取下拉菜单中的所有选项
        destinations = []
        
        # 尝试获取所有下拉列表
        for i in range(await lists.count()):
            items = lists.nth(i).locator('li')
            count = await items.count()
            print(f"  列表 {i+1}: {count} 个选项", flush=True)
            
            for j in range(count):
                try:
                    item = items.nth(j)
                    if await item.is_visible():
                        text = await item.inner_text()
                        # 提取机场代码和城市名
                        # 格式通常是 "City Name (Airport Code)" 或 "Airport Code - City Name"
                        destinations.append(text.strip())
                except Exception as e:
                    pass
        
        print(f"\n✅ 找到 {len(destinations)} 个目的地\n", flush=True)
        
        # 打印所有目的地
        print("=" * 70)
        print("可用目的地列表:")
        print("=" * 70)
        
        # 解析并格式化目的地
        parsed_dests = []
        for dest in destinations:
            if dest and len(dest) > 0:
                print(f"  {dest}", flush=True)
                # 尝试提取机场代码（通常是 3 个大写字母）
                import re
                match = re.search(r'\(([A-Z]{3})\)', dest)
                if match:
                    code = match.group(1)
                    # 提取城市名
                    city = dest.split('(')[0].strip()
                    parsed_dests.append((code, city))
                else:
                    # 尝试其他格式
                    parts = dest.split(' - ')
                    if len(parts) >= 2:
                        code = parts[0].strip()
                        city = parts[1].strip()
                        parsed_dests.append((code, city))
        
        print("\n" + "=" * 70)
        print(f"解析后的目的地（{len(parsed_dests)} 个）:")
        print("=" * 70)
        for code, city in parsed_dests:
            print(f'  ("{code}", "{city}"),', flush=True)
        
        # 保存到文件
        output_file = f"destinations_{ORIGIN_CODE}.txt"
        with open(output_file, 'w') as f:
            f.write(f"# {ORIGIN_CODE} ({ORIGIN_NAME}) 出发的可用目的地\n\n")
            f.write("DESTS = [\n")
            for code, city in parsed_dests:
                f.write(f'    ("{code}", "{city}"),\n')
            f.write("]\n")
        
        print(f"\n📁 已保存到: {output_file}", flush=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
