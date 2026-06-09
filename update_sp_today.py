#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════╗
║  سكربت تحديث بيانات سعر الليرة السورية                        ║
║  من موقع sp-today.com                                          ║
║  الإصدار 3.0 - النسخة النهائية المحسّنة                        ║
║                                                                ║
║  المهندس الاستشاري احمد عمران                                  ║
║  سوريا - طرطوس                                                 ║
║  © 2026 - جميع الحقوق محفوظة                                  ║
╚════════════════════════════════════════════════════════════════╝
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import sys
import os
import shutil
import subprocess
import time
import random

# ═══════════════════════════════════════════════════════════════
#                      الإعدادات العامة
# ═══════════════════════════════════════════════════════════════

DATA_FILE = 'sp_today_data.json'
BACKUP_FILE = 'sp_today_data.backup.json'
LOG_FILE = 'update_log.txt'
TARGET_URL = 'https://sp-today.com/'
TIMEOUT = 30
MAX_NEWS = 5

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}


# ═══════════════════════════════════════════════════════════════
#                      دوال مساعدة
# ═══════════════════════════════════════════════════════════════

def log(message, level='INFO'):
    """تسجيل العمليات مع الوقت"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    icons = {
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'START': '🚀',
        'SAVE': '💾'
    }
    icon = icons.get(level, '•')
    log_msg = f"[{timestamp}] {icon} {message}"
    print(log_msg)

    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    except Exception as e:
        print(f"فشل التسجيل: {e}")


def print_separator(char='═', length=60):
    """طباعة فاصل"""
    print(char * length)


def print_header():
    """طباعة الترويسة"""
    print_separator()
    print("🔄 سكربت تحديث أسعار الليرة السورية - الإصدار 3.0")
    print("👨‍💼 المهندس الاستشاري احمد عمران")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()


# ═══════════════════════════════════════════════════════════════
#                      النسخ الاحتياطي
# ═══════════════════════════════════════════════════════════════

def backup_data():
    """إنشاء نسخة احتياطية من الملف الحالي"""
    if os.path.exists(DATA_FILE):
        try:
            shutil.copy(DATA_FILE, BACKUP_FILE)
            log(f"تم إنشاء نسخة احتياطية: {BACKUP_FILE}", 'SAVE')
            return True
        except Exception as e:
            log(f"فشل إنشاء النسخة الاحتياطية: {e}", 'ERROR')
            return False
    else:
        log("لا يوجد ملف سابق للنسخ الاحتياطي", 'INFO')
        return True


# ═══════════════════════════════════════════════════════════════
#                      جلب البيانات
# ═══════════════════════════════════════════════════════════════

def fetch_html():
    """جلب HTML من الموقع مع إعادة المحاولة"""
    log(f"جاري الاتصال بـ {TARGET_URL}...", 'START')

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            # تأخير عشوائي
            if attempt > 1:
                time.sleep(random.uniform(2, 5))

            response = requests.get(
                TARGET_URL,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=True
            )
            response.encoding = 'utf-8'

            if response.status_code == 200:
                log(f"تم الاتصال بنجاح (HTTP {response.status_code})", 'SUCCESS')
                log(f"حجم HTML: {len(response.text):,} حرف", 'INFO')
                return response.text
            else:
                log(f"HTTP {response.status_code} - المحاولة {attempt}/{max_retries}", 'WARNING')

        except requests.exceptions.Timeout:
            log(f"انتهت مهلة الاتصال - المحاولة {attempt}/{max_retries}", 'WARNING')
        except requests.exceptions.ConnectionError:
            log(f"فشل الاتصال - المحاولة {attempt}/{max_retries}", 'WARNING')
        except Exception as e:
            log(f"خطأ: {e} - المحاولة {attempt}/{max_retries}", 'WARNING')

    log("فشلت جميع المحاولات", 'ERROR')
    return None


# ═══════════════════════════════════════════════════════════════
#                      استخراج العملات
# ═══════════════════════════════════════════════════════════════

def extract_currencies(text):
    """استخراج أسعار العملات - نسخة ذكية مع نطاقات سعرية"""
    log("جاري استخراج أسعار العملات...", 'INFO')

    currencies = []

    # قائمة العملات مع النطاقات السعرية المتوقعة
    currency_config = [
        {'code': 'USD', 'name': 'دولار امريكي', 'flag': '🇺🇸', 'min': 10000, 'max': 20000},
        {'code': 'EUR', 'name': 'يورو', 'flag': '🇪🇺', 'min': 12000, 'max': 25000},
        {'code': 'TRY', 'name': 'ليرة تركية', 'flag': '🇹🇷', 'min': 200, 'max': 800},
        {'code': 'SAR', 'name': 'ريال سعودي', 'flag': '🇸🇦', 'min': 3000, 'max': 5000},
        {'code': 'AED', 'name': 'درهم اماراتي', 'flag': '🇦🇪', 'min': 3000, 'max': 5000},
        {'code': 'EGP', 'name': 'جنيه مصري', 'flag': '🇪🇬', 'min': 200, 'max': 500},
        {'code': 'LYD', 'name': 'دينار ليبي', 'flag': '🇱🇾', 'min': 1500, 'max': 3000},
        {'code': 'JOD', 'name': 'دينار اردني', 'flag': '🇯🇴', 'min': 15000, 'max': 25000},
        {'code': 'KWD', 'name': 'دينار كويتي', 'flag': '🇰🇼', 'min': 35000, 'max': 50000},
        {'code': 'GBP', 'name': 'جنيه استرليني', 'flag': '🇬🇧', 'min': 15000, 'max': 25000},
        {'code': 'QAR', 'name': 'ريال قطري', 'flag': '🇶🇦', 'min': 3000, 'max': 5000},
        {'code': 'BHD', 'name': 'دينار بحريني', 'flag': '🇧🇭', 'min': 30000, 'max': 45000},
        {'code': 'SEK', 'name': 'كرونة سويدية', 'flag': '🇸🇪', 'min': 1000, 'max': 2500},
        {'code': 'CAD', 'name': 'دولار كندي', 'flag': '🇨🇦', 'min': 8000, 'max': 15000},
        {'code': 'OMR', 'name': 'ريال عماني', 'flag': '🇴🇲', 'min': 30000, 'max': 45000},
        {'code': 'NOK', 'name': 'كرونة نرويجية', 'flag': '🇳🇴', 'min': 1000, 'max': 2500},
        {'code': 'DKK', 'name': 'كرونة دنماركية', 'flag': '🇩🇰', 'min': 1500, 'max': 3000},
        {'code': 'DZD', 'name': 'دينار جزائري', 'flag': '🇩🇿', 'min': 50, 'max': 200},
        {'code': 'MAD', 'name': 'درهم مغربي', 'flag': '🇲🇦', 'min': 1000, 'max': 2500},
        {'code': 'TND', 'name': 'دينار تونسي', 'flag': '🇹🇳', 'min': 3000, 'max': 6000},
        {'code': 'RUB', 'name': 'روبل روسي', 'flag': '🇷🇺', 'min': 100, 'max': 400},
        {'code': 'MYR', 'name': 'رينغيت ماليزي', 'flag': '🇲🇾', 'min': 2500, 'max': 5000},
        {'code': 'BRL', 'name': 'ريال برازيلي', 'flag': '🇧🇷', 'min': 2000, 'max': 4000},
        {'code': 'NZD', 'name': 'دولار نيوزيلندي', 'flag': '🇳🇿', 'min': 6000, 'max': 12000},
        {'code': 'CHF', 'name': 'فرنك سويسري', 'flag': '🇨🇭', 'min': 12000, 'max': 22000},
        {'code': 'AUD', 'name': 'دولار استرالي', 'flag': '🇦🇺', 'min': 7000, 'max': 14000},
        {'code': 'ZAR', 'name': 'راند جنوب افريقي', 'flag': '🇿🇦', 'min': 600, 'max': 1500},
        {'code': 'IQD', 'name': 'دينار عراقي', 'flag': '🇮🇶', 'min': 5, 'max': 20},
        {'code': 'SGD', 'name': 'دولار سنغافوري', 'flag': '🇸🇬', 'min': 8000, 'max': 15000},
    ]

    # البحث عن قسم الأسعار
    currency_section = text.find('الأسعار الحالية')
    if currency_section == -1:
        currency_section = text.find('اسعار العملات')

    if currency_section == -1:
        log("لم يتم العثور على قسم العملات", 'WARNING')
        return currencies

    currency_text = text[currency_section:currency_section + 10000]

    # استخراج مواقع أكواد العملات
    code_positions = []
    for config in currency_config:
        code = config['code']
        pos = currency_text.find(code)
        if pos != -1:
            code_positions.append((pos, config))

    # ترتيب حسب الموقع
    code_positions.sort(key=lambda x: x[0])

    # استخراج الأسعار لكل عملة
    for i, (pos, config) in enumerate(code_positions):
        code = config['code']

        # تحديد نهاية الجزء
        if i + 1 < len(code_positions):
            end_pos = code_positions[i + 1][0]
        else:
            end_pos = pos + 300

        snippet = currency_text[pos:end_pos]

        # استخراج جميع الأرقام
        all_numbers = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)', snippet)

        # تحويل الأرقام وإزالة التكرارات
        numbers = []
        seen = set()
        for num_str in all_numbers:
            try:
                num = int(num_str.replace(',', ''))
                if 1 <= num <= 100000 and num not in seen:
                    numbers.append(num)
                    seen.add(num)
            except ValueError:
                continue

        if len(numbers) >= 2:
            # اختيار الأرقام التي تقع في النطاق المتوقع
            valid_numbers = [n for n in numbers if config['min'] <= n <= config['max']]

            if len(valid_numbers) >= 2:
                buy = valid_numbers[0]
                sell = valid_numbers[1]
            else:
                buy = numbers[0]
                sell = numbers[1]

            # استخراج نسبة التغيير
            change_match = re.search(r'([+-]?\d+\.?\d*)\s*%', snippet)
            if change_match:
                change = f"{change_match.group(1)}%"
                change_up = not change_match.group(1).startswith('-')
            else:
                change = '+0.00%'
                change_up = True

            # التحقق من المعقولية النهائية
            if config['min'] * 0.5 <= buy <= config['max'] * 2 and \
                    config['min'] * 0.5 <= sell <= config['max'] * 2:
                currencies.append({
                    'code': code,
                    'name': config['name'],
                    'flag': config['flag'],
                    'buy': buy,
                    'sell': sell,
                    'change': change,
                    'changeUp': change_up
                })
                log(f"{code}: شراء {buy:,} | مبيع {sell:,} | {change}", 'SUCCESS')
            else:
                log(f"{code}: أرقام غير منطقية ({buy}, {sell})", 'WARNING')
        else:
            log(f"{code}: لم يتم العثور على أرقام كافية ({len(numbers)})", 'WARNING')

    log(f"تم استخراج {len(currencies)} عملة", 'SUCCESS')
    return currencies


# ═══════════════════════════════════════════════════════════════
#                      استخراج الذهب
# ═══════════════════════════════════════════════════════════════

def extract_gold(text):
    """استخراج أسعار الذهب - نسخة محسّنة"""
    log("جاري استخراج أسعار الذهب...", 'INFO')

    gold = []

    gold_section = text.find('أسعار الذهب')
    if gold_section == -1:
        gold_section = text.find('اسعار الذهب')

    if gold_section == -1:
        log("لم يتم العثور على قسم الذهب", 'WARNING')
        return gold

    gold_text = text[gold_section:gold_section + 3000]

    karats_config = [
        {'karat': '24K', 'min_gram': 100, 'max_gram': 200, 'min_price': 1500000, 'max_price': 3000000},
        {'karat': '21K', 'min_gram': 80, 'max_gram': 180, 'min_price': 1200000, 'max_price': 2500000},
        {'karat': '18K', 'min_gram': 70, 'max_gram': 150, 'min_price': 1000000, 'max_price': 2000000},
        {'karat': '14K', 'min_gram': 50, 'max_gram': 120, 'min_price': 800000, 'max_price': 1500000},
    ]

    for config in karats_config:
        karat = config['karat']

        karat_pos = gold_text.find(karat)
        if karat_pos == -1:
            log(f"{karat}: لم يتم العثور على العيار", 'WARNING')
            continue

        snippet = gold_text[karat_pos:karat_pos + 300]

        # استخراج السعر بالدولار
        gram_usd_match = re.search(r'\$?\s*(\d+\.\d+)', snippet)
        gram_usd = float(gram_usd_match.group(1)) if gram_usd_match else 0

        # استخراج جميع الأرقام
        all_numbers = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)', snippet)

        prices = []
        for num_str in all_numbers:
            try:
                num = int(num_str.replace(',', ''))
                if config['min_price'] <= num <= config['max_price']:
                    prices.append(num)
            except ValueError:
                continue

        if len(prices) >= 2:
            buy = prices[0]
            sell = prices[1]

            gold.append({
                'karat': karat,
                'gramUsd': gram_usd,
                'buy': buy,
                'sell': sell
            })
            log(f"{karat}: ${gram_usd} | شراء {buy:,} | مبيع {sell:,}", 'SUCCESS')
        else:
            log(f"{karat}: لم يتم العثور على أسعار صحيحة", 'WARNING')

    log(f"تم استخراج {len(gold)} أسعار ذهب", 'SUCCESS')
    return gold

# ═══════════════════════════════════════════════════════════════
#                      استخراج الأخبار
# ═══════════════════════════════════════════════════════════════

def extract_news(text):
    """استخراج الأخبار الاقتصادية"""
    log("جاري استخراج الأخبار...", 'INFO')

    news = []

    news_section = text.find('أخبار اقتصادية')
    if news_section == -1:
        news_section = text.find('اخبار اقتصادية')

    if news_section == -1:
        log("لم يتم العثور على قسم الأخبار", 'WARNING')
        return news

    news_text = text[news_section:news_section + 5000]

    # استخراج الأخبار
    news_items = re.findall(
        r'(\d{1,2}/\d{1,2}/\d{4})\s*[-–—]?\s*(.+?)(?=\n\d{1,2}/\d{1,2}/\d{4}|\Z)',
        news_text,
        re.DOTALL
    )

    for date, title_desc in news_items[:MAX_NEWS]:
        lines = title_desc.strip().split('\n')
        title = lines[0].strip() if lines else ''
        desc = ' '.join(lines[1:]).strip() if len(lines) > 1 else ''

        if title:
            news.append({
                'date': date.strip().replace('‏', ''),
                'title': title[:100],
                'desc': desc[:300]
            })
            log(f"خبر: {title[:50]}...", 'SUCCESS')

    log(f"تم استخراج {len(news)} أخبار", 'SUCCESS')
    return news


# ═══════════════════════════════════════════════════════════════
#                      جلب البيانات الرئيسية
# ═══════════════════════════════════════════════════════════════

def fetch_data():
    """جلب جميع البيانات من الموقع"""
    html = fetch_html()
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()

    data = {
        'lastUpdate': datetime.now().isoformat(),
        'currencies': extract_currencies(text),
        'gold': extract_gold(text),
        'news': extract_news(text),
        'source': 'sp-today.com'
    }

    return data


# ═══════════════════════════════════════════════════════════════
#                      البيانات الافتراضية
# ═══════════════════════════════════════════════════════════════

def load_default_data():
    """تحميل البيانات الافتراضية"""
    log("تحميل البيانات الافتراضية...", 'INFO')

    return {
        'lastUpdate': datetime.now().isoformat(),
        'currencies': [
            {'code': 'USD', 'name': 'دولار امريكي', 'flag': '🇺🇸', 'buy': 14340, 'sell': 14390, 'change': '+0.92%',
             'changeUp': True},
            {'code': 'EUR', 'name': 'يورو', 'flag': '🇪🇺', 'buy': 16440, 'sell': 16640, 'change': '+1.05%',
             'changeUp': True},
            {'code': 'TRY', 'name': 'ليرة تركية', 'flag': '🇹🇷', 'buy': 307, 'sell': 311, 'change': '+0.66%',
             'changeUp': True},
            {'code': 'SAR', 'name': 'ريال سعودي', 'flag': '🇸🇦', 'buy': 3766, 'sell': 3820, 'change': '+0.91%',
             'changeUp': True},
            {'code': 'AED', 'name': 'درهم اماراتي', 'flag': '🇦🇪', 'buy': 3849, 'sell': 3905, 'change': '+0.92%',
             'changeUp': True},
            {'code': 'EGP', 'name': 'جنيه مصري', 'flag': '🇪🇬', 'buy': 273, 'sell': 277, 'change': '+1.49%',
             'changeUp': True},
        ],
        'gold': [
            {'karat': '24K', 'gramUsd': 139.00, 'buy': 1989200, 'sell': 2013700},
            {'karat': '21K', 'gramUsd': 122.00, 'buy': 1740600, 'sell': 1762000},
            {'karat': '18K', 'gramUsd': 104.00, 'buy': 1491900, 'sell': 1510300},
            {'karat': '14K', 'gramUsd': 81.00, 'buy': 1160300, 'sell': 1174600}
        ],
        'news': [
            {'date': datetime.now().strftime('%d/%m/%Y'), 'title': 'تحديث الأسعار',
             'desc': 'تم تحديث أسعار العملات والذهب بنجاح'}
        ],
        'source': 'default'
    }


# ═══════════════════════════════════════════════════════════════
#                      التحقق والمعالجة
# ═══════════════════════════════════════════════════════════════

def validate_data(data):
    """التحقق من صحة البيانات المستخرجة"""
    if not data:
        log("لا توجد بيانات للتحقق", 'ERROR')
        return False

    currencies = data.get('currencies', [])
    if len(currencies) < 5:
        log(f"عدد العملات قليل جداً: {len(currencies)}", 'WARNING')
        return False

    for c in currencies:
        if c['sell'] < 1 or c['sell'] > 200000:
            log(f"سعر غير منطقي لـ {c['code']}: {c['sell']}", 'WARNING')
            return False

    gold = data.get('gold', [])
    if len(gold) < 3:
        log(f"عدد أسعار الذهب قليل: {len(gold)}", 'WARNING')

    log("البيانات صحيحة", 'SUCCESS')
    return True


def calculate_changes(new_data):
    """حساب نسبة التغيير مقارنة بالبيانات السابقة"""
    if not os.path.exists(DATA_FILE):
        log("لا توجد بيانات سابقة لحساب التغييرات", 'INFO')
        return new_data

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)

        old_map = {c['code']: c['sell'] for c in old_data.get('currencies', [])}

        if not old_map:
            return new_data

        changes_count = 0
        for currency in new_data.get('currencies', []):
            code = currency['code']
            if code in old_map and old_map[code] > 0:
                old_price = old_map[code]
                new_price = currency['sell']

                change = ((new_price - old_price) / old_price) * 100
                currency['change'] = f"{'+' if change >= 0 else ''}{change:.2f}%"
                currency['changeUp'] = change >= 0
                changes_count += 1

        log(f"تم حساب التغييرات لـ {changes_count} عملة", 'SUCCESS')

    except Exception as e:
        log(f"خطأ في حساب التغييرات: {e}", 'WARNING')

    return new_data


# ═══════════════════════════════════════════════════════════════
#                      الحفظ والنشر
# ═══════════════════════════════════════════════════════════════

def save_data(data, filename=DATA_FILE):
    """حفظ البيانات في ملف JSON"""
    if not data:
        log("لا توجد بيانات للحفظ", 'ERROR')
        return False

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        file_size = os.path.getsize(filename)
        log(f"تم حفظ البيانات في {filename} ({file_size:,} بايت)", 'SAVE')
        log(f"آخر تحديث: {data.get('lastUpdate', 'غير محدد')}", 'INFO')

        return True

    except Exception as e:
        log(f"خطأ في الحفظ: {e}", 'ERROR')
        return False


def push_to_github():
    """رفع التغييرات إلى GitHub"""
    try:
        log("جاري الرفع إلى GitHub...", 'START')

        result = subprocess.run(['git', '--version'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            log("Git غير مثبت", 'WARNING')
            return False

        subprocess.run(['git', 'add', DATA_FILE],
                       check=True, capture_output=True, timeout=10)

        result = subprocess.run(['git', 'status', '--porcelain'],
                                capture_output=True, text=True, timeout=5)
        if not result.stdout.strip():
            log("لا توجد تغييرات للرفع", 'INFO')
            return True

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        commit_msg = f'🔄 تحديث الأسعار - {timestamp}'
        subprocess.run(['git', 'commit', '-m', commit_msg],
                       check=True, capture_output=True, timeout=10)

        subprocess.run(['git', 'push'],
                       check=True, capture_output=True, timeout=30)

        log("تم الرفع إلى GitHub بنجاح!", 'SUCCESS')
        return True

    except subprocess.CalledProcessError as e:
        log(f"فشل الرفع: {e.stderr.decode() if e.stderr else str(e)}", 'ERROR')
        return False
    except Exception as e:
        log(f"خطأ في Git: {e}", 'ERROR')
        return False


# ═══════════════════════════════════════════════════════════════
#                      التقرير النهائي
# ═══════════════════════════════════════════════════════════════

def print_report(data):
    """طباعة التقرير النهائي"""
    print_separator()
    print("📊 التقرير النهائي:")
    print_separator()

    currencies = data.get('currencies', [])
    print(f"💰 العملات المستخرجة: {len(currencies)}")
    if currencies:
        print("\nأهم 5 عملات:")
        for c in currencies[:5]:
            arrow = '📈' if c.get('changeUp', True) else '📉'
            print(f"  {c['flag']} {c['code']}: {c['buy']:,} → {c['sell']:,} {arrow} {c.get('change', 'N/A')}")

    gold = data.get('gold', [])
    print(f"\n🥇 أسعار الذهب: {len(gold)}")
    if gold:
        for g in gold:
            print(f"  {g['karat']}: ${g['gramUsd']} | {g['buy']:,} → {g['sell']:,}")

    news = data.get('news', [])
    print(f"\n📰 الأخبار: {len(news)}")
    if news:
        for i, n in enumerate(news[:3], 1):
            print(f"  {i}. {n['title'][:60]}...")

    print_separator()
    print(f"✅ المصدر: {data.get('source', 'غير محدد')}")
    print(f"📅 التحديث: {data.get('lastUpdate', 'غير محدد')}")
    print_separator()


# ═══════════════════════════════════════════════════════════════
#                      الدالة الرئيسية
# ═══════════════════════════════════════════════════════════════

def main():
    """الدالة الرئيسية"""
    print_header()

    start_time = time.time()

    try:
        # 1. إنشاء نسخة احتياطية
        backup_data()

        # 2. جلب البيانات
        data = fetch_data()

        # 3. التحقق من البيانات
        if data and validate_data(data):
            log("تم جلب البيانات بنجاح", 'SUCCESS')
        else:
            log("فشل جلب البيانات، استخدام البيانات الافتراضية", 'WARNING')
            data = load_default_data()

        # 4. حساب التغييرات
        data = calculate_changes(data)

        # 5. حفظ البيانات
        if not save_data(data):
            log("فشل حفظ البيانات", 'ERROR')
            return 1

        # 6. رفع إلى GitHub (اختياري)
        if '--push' in sys.argv or '--all' in sys.argv:
            push_to_github()

        # 7. التقرير النهائي
        print_report(data)

        # حساب الوقت المستغرق
        elapsed = time.time() - start_time
        log(f"الوقت المستغرق: {elapsed:.2f} ثانية", 'INFO')

        print_separator()
        print("✅ تم الانتهاء بنجاح!")
        print_separator()

        return 0

    except KeyboardInterrupt:
        log("تم إلغاء العملية بواسطة المستخدم", 'WARNING')
        return 1
    except Exception as e:
        log(f"خطأ غير متوقع: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
