#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تحديث أسعار العملات من sp-today.com
يعمل مع GitHub Actions لتحديث تلقائي
"""

import json
import os
import sys
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ====== إعدادات ======
TARGET_URL = "https://sp-today.com/"
DATA_FILE = "sp_today_data.json"
TIMEOUT = 30

# User-Agent لتجنب الحظر
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en;q=0.5',
}

# ====== دوال مساعدة ======
def fetch_html(url):
    """جلب HTML من الموقع"""
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=TIMEOUT) as response:
            return response.read().decode('utf-8', errors='ignore')
    except (URLError, HTTPError) as e:
        print(f"❌ خطأ في جلب البيانات: {e}")
        return None

def parse_prices(html):
    """استخراج أسعار العملات من HTML"""
    currencies = []
    
    # محاولة استخراج من JSON داخل السكريبت
    json_patterns = [
        r'var\s+data\s*=\s*(\{[^}]+\})',
        r'"currencies"\s*:\s*(\[[\s\S]*?\])',
        r'window\.__DATA__\s*=\s*(\{[^}]+\})',
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, html)
        if match:
            try:
                data = json.loads(match.group(1))
                if 'currencies' in data:
                    return data
            except json.JSONDecodeError:
                continue
    
    # محاولة استخراج من الجداول
    # نمط: <td>اسم العملة</td><td>سعر الشراء</td><td>سعر البيع</td>
    table_rows = re.findall(
        r'<tr[^>]*>.*?<td[^>]*>([^<]+)</td>.*?<td[^>]*>([\d,]+)</td>.*?<td[^>]*>([\d,]+)</td>.*?</tr>',
        html, re.DOTALL
    )
    
    if table_rows:
        for row in table_rows:
            name, buy, sell = row
            buy = int(buy.replace(',', ''))
            sell = int(sell.replace(',', ''))
            if buy > 0 and sell > 0:
                currencies.append({
                    'name': name.strip(),
                    'buy': buy,
                    'sell': sell
                })
    
    return currencies

def parse_gold(html):
    """استخراج أسعار الذهب"""
    gold = []
    
    # نمط أسعار الذهب
    gold_pattern = re.findall(
        r'(\d+K).*?(?:غرام|gram).*?\$?([\d.]+).*?([\d,]+).*?([\d,]+)',
        html, re.DOTALL
    )
    
    for match in gold_pattern:
        karat, gram_usd, buy, sell = match
        gold.append({
            'karat': karat,
            'gramUsd': float(gram_usd),
            'buy': int(buy.replace(',', '')),
            'sell': int(sell.replace(',', ''))
        })
    
    return gold

def parse_news(html):
    """استخراج الأخبار"""
    news = []
    
    # نمط الأخبار
    news_pattern = re.findall(
        r'<div[^>]*class="news[^"]*"[^>]*>.*?<span[^>]*>(\d+/\d+/\d+)</span>.*?<h[23][^>]*>([^<]+)</h[23]>.*?<p[^>]*>([^<]+)</p>',
        html, re.DOTALL
    )
    
    for match in news_pattern:
        date, title, desc = match
        news.append({
            'date': date.strip(),
            'title': title.strip(),
            'desc': desc.strip()
        })
    
    return news[:5]  # آخر 5 أخبار فقط

def load_existing_data():
    """تحميل البيانات الحالية كـ fallback"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None

def save_data(data):
    """حفظ البيانات في ملف JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ تم حفظ البيانات في {DATA_FILE}")

def main():
    print(f"🔄 بدء التحديث - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # تحميل البيانات الحالية
    existing_data = load_existing_data()
    if not existing_data:
        print("⚠️ لا توجد بيانات سابقة، سيتم إنشاء بيانات افتراضية")
        existing_data = {
            'currencies': [],
            'gold': [],
            'news': [],
            'lastUpdate': None,
            'source': 'unknown'
        }
    
    # جلب HTML من الموقع
    print(f"📡 جاري الاتصال بـ {TARGET_URL}...")
    html = fetch_html(TARGET_URL)
    
    if not html:
        print("❌ فشل في جلب البيانات من الموقع")
        print("⚠️ سيتم الاحتفاظ بالبيانات الحالية وتحديث الوقت فقط")
        existing_data['lastUpdate'] = datetime.now(timezone.utc).isoformat()
        existing_data['source'] = 'fallback (connection failed)'
        save_data(existing_data)
        sys.exit(1)
    
    print("📊 جاري تحليل البيانات...")
    
    # استخراج الأسعار
    currencies = parse_prices(html)
    gold = parse_gold(html)
    news = parse_news(html)
    
    # تحديث البيانات
    updated = False
    
    if currencies:
        existing_data['currencies'] = currencies
        updated = True
        print(f"✅ تم استخراج {len(currencies)} عملة")
    else:
        print("️ لم يتم استخراج أسعار العملات")
    
    if gold:
        existing_data['gold'] = gold
        updated = True
        print(f"✅ تم استخراج {len(gold)} عيار ذهب")
    
    if news:
        existing_data['news'] = news
        updated = True
        print(f"✅ تم استخراج {len(news)} خبر")
    
    # تحديث وقت آخر تحديث
    existing_data['lastUpdate'] = datetime.now(timezone.utc).isoformat()
    existing_data['source'] = 'sp-today.com'
    
    if updated:
        save_data(existing_data)
        print(" تم التحديث بنجاح!")
    else:
        print("⚠️ لم يتم استخراج بيانات جديدة، تم الاحتفاظ بالبيانات الحالية")
        save_data(existing_data)
    
    return 0 if updated else 1

if __name__ == '__main__':
    sys.exit(main())
