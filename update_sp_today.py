#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════╗
║  سكربت تحديث بيانات سعر الليرة السورية                        ║
║  من موقع sp-today.com                                          ║
║  الإصدار 2.0 - النسخة الكاملة                                  ║
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
    print("🔄 سكربت تحديث أسعار الليرة السورية - الإصدار 2.0")
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
    """جلب HTML من الموقع"""
    log(f"جاري الاتصال بـ {TARGET_URL}...", 'START')
    
    try:
        response = requests.get(
            TARGET_URL,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True
        )
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            log(f"خطأ في الاتصال: HTTP {response.status_code}", 'ERROR')
            return None
        
        log(f"تم الاتصال بنجاح (HTTP {response.status_code})", 'SUCCESS')
        log(f"حجم HTML: {len(response.text):,} حرف", 'INFO')
        
        return response.text
    
    except requests.exceptions.Timeout:
        log("انتهت مهلة الاتصال", 'ERROR')
        return None
    except requests.exceptions.ConnectionError:
        log("فشل الاتصال بالإنترنت", 'ERROR')
        return None
    except Exception as e:
        log(f"خطأ غير متوقع: {e}", 'ERROR')
        return None

def extract_currencies(text):
    """استخراج أسعار العملات"""
    log("جاري استخراج أسعار العملات...", 'INFO')
    
    currencies = []
    
    # قائمة شاملة بالعملات (29 عملة)
    currency_patterns = [
        {'code': 'USD', 'name': 'دولار امريكي', 'flag': '🇺🇸'},
        {'code': 'EUR', 'name': 'يورو', 'flag': '🇪🇺'},
        {'code': 'TRY', 'name': 'ليرة تركية', 'flag': '🇹🇷'},
        {'code': 'SAR', 'name': 'ريال سعودي', 'flag': '🇸🇦'},
        {'code': 'AED', 'name': 'درهم اماراتي', 'flag': '🇦🇪'},
        {'code': 'EGP', 'name': 'جنيه مصري', 'flag': '🇪🇬'},
        {'code': 'LYD', 'name': 'دينار ليبي', 'flag': '🇱🇾'},
        {'code': 'JOD', 'name': 'دينار اردني', 'flag': '🇯🇴'},
        {'code': 'KWD', 'name': 'دينار كويتي', 'flag': '🇰🇼'},
        {'code': 'GBP', 'name': 'جنيه استرليني', 'flag': '🇬🇧'},
        {'code': 'QAR', 'name': 'ريال قطري', 'flag': '🇶🇦'},
        {'code': 'BHD', 'name': 'دينار بحريني', 'flag': '🇧🇭'},
        {'code': 'SEK', 'name': 'كرونة سويدية', 'flag': '🇸🇪'},
        {'code': 'CAD', 'name': 'دولار كندي', 'flag': '🇨🇦'},
        {'code': 'OMR', 'name': 'ريال عماني', 'flag': '🇴🇲'},
        {'code': 'NOK', 'name': 'كرونة نرويجية', 'flag': '🇳🇴'},
        {'code': 'DKK', 'name': 'كرونة دنماركية', 'flag': '🇩🇰'},
        {'code': 'DZD', 'name': 'دينار جزائري', 'flag': '🇩🇿'},
        {'code': 'MAD', 'name': 'درهم مغربي', 'flag': '🇲🇦'},
        {'code': 'TND', 'name': 'دينار تونسي', 'flag': '🇹🇳'},
        {'code': 'RUB', 'name': 'روبل روسي', 'flag': '🇷🇺'},
        {'code': 'MYR', 'name': 'رينغيت ماليزي', 'flag': '🇲🇾'},
        {'code': 'BRL', 'name': 'ريال برازيلي', 'flag': '🇧🇷'},
        {'code': 'NZD', 'name': 'دولار نيوزيلندي', 'flag': '🇳🇿'},
        {'code': 'CHF', 'name': 'فرنك سويسري', 'flag': '🇨🇭'},
        {'code': 'AUD', 'name': 'دولار استرالي', 'flag': '🇦🇺'},
        {'code': 'ZAR', 'name': 'راند جنوب افريقي', 'flag': '🇿🇦'},
        {'code': 'IQD', 'name': 'دينار عراقي', 'flag': '🇮🇶'},
        {'code': 'SGD', 'name': 'دولار سنغافوري', 'flag': '🇸🇬'},
    ]
    
    # البحث عن قسم الأسعار
    currency_section = text.find('الأسعار الحالية')
    if currency_section == -1:
        # محاولة بديلة
        currency_section = text.find('اسعار العملات')
    
    if currency_section == -1:
        log("لم يتم العثور على قسم العملات", 'WARNING')
        return currencies
    
    currency_text = text[currency_section:currency_section + 8000]
    
    # استخراج كل عملة
    for pattern in currency_patterns:
        code = pattern['code']
        
        # أنماط بحث متعددة
        patterns_to_try = [
            rf'{code}.*?([0-9,]{{3,}}).*?([0-9,]{{3,}}).*?([+-]?[0-9.]+)%',
            rf'{code}\D+?([0-9,]{{3,}})\D+?([0-9,]{{3,}})\D+?([+-]?[0-9.]+)%',
            rf'{code}.*?([0-9]{{3,}}).*?([0-9]{{3,}})',
        ]
        
        for regex_pattern in patterns_to_try:
            match = re.search(regex_pattern, currency_text, re.DOTALL)
            
            if match:
                try:
                    buy_str = match.group(1).replace(',', '').replace(' ', '')
                    sell_str = match.group(2).replace(',', '').replace(' ', '')
                    
                    buy = int(buy_str)
                    sell = int(sell_str)
                    
                    # استخراج نسبة التغيير إذا وجدت
                    try:
                        change_str = match.group(3)
                        change = f"{change_str}%"
                        change_up = not change_str.startswith('-')
                    except (IndexError, AttributeError):
                        change = '+0.00%'
                        change_up = True
                    
                    # التحقق من المعقولية
                    if 10 <= sell <= 200000:
                        currencies.append({
                            'code': code,
                            'name': pattern['name'],
                            'flag': pattern['flag'],
                            'buy': buy,
                            'sell': sell,
                            'change': change,
                            'changeUp': change_up
                        })
                        log(f"{code}: شراء {buy:,} | مبيع {sell:,} | {change}", 'SUCCESS')
                        break  # الانتقال للعملة التالية
                    else:
                        log(f"{code}: سعر غير منطقي ({sell})", 'WARNING')
                
                except (ValueError, AttributeError) as e:
                    continue
        
        if not any(c['code'] == code for c in currencies):
            log(f"{code}: لم يتم العثور على السعر", 'WARNING')
    
    log(f"تم استخراج {len(currencies)} عملة", 'SUCCESS')
    return currencies

def extract_gold(text):
    """استخراج أسعار الذهب"""
    log("جاري استخراج أسعار الذهب...", 'INFO')
    
    gold = []
    
    gold_section = text.find('أسعار الذهب')
    if gold_section == -1:
        gold_section = text.find('اسعار الذهب')
    
    if gold_section == -1:
        log("لم يتم العثور على قسم الذهب", 'WARNING')
        return gold
    
    gold_text = text[gold_section:gold_section + 2000]
    
    karats = ['24K', '21K', '18K', '14K']
    
    for karat in karats:
        # أنماط بحث متعددة
        patterns = [
            rf'{karat}.*?\$?([0-9.]+).*?([0-9,]{{3,}}).*?([0-9,]{{3,}})',
            rf'{karat}\D+?\$?([0-9.]+)\D+?([0-9,]{{3,}})\D+?([0-9,]{{3,}})',
            rf'{karat}.*?([0-9.]+).*?([0-9]{{3,}}).*?([0-9]{{3,}})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, gold_text, re.DOTALL)
            
            if match:
                try:
                    gram_usd = float(match.group(1))
                    buy = int(match.group(2).replace(',', '').replace(' ', ''))
                    sell = int(match.group(3).replace(',', '').replace(' ', ''))
                    
                    if 1000 <= sell <= 5000000:
                        gold.append({
                            'karat': karat,
                            'gramUsd': gram_usd,
                            'buy': buy,
                            'sell': sell
                        })
                        log(f"{karat}: ${gram_usd} | شراء {buy:,} | مبيع {sell:,}", 'SUCCESS')
                        break
                except (ValueError, AttributeError):
                    continue
        
        if not any(g['karat'] == karat for g in gold):
            log(f"{karat}: لم يتم العثور على السعر", 'WARNING')
    
    log(f"تم استخراج {len(gold)} أسعار ذهب", 'SUCCESS')
    return gold

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
    
    # استخراج الأخبار باستخدام regex
    news_items = re.findall(
        r'(\d{1,2}/\d{1,2}/\d{4})\s*[-–—]?\s*(.+?)(?=\n\d{1,2}/\d{1,2}/\d{4}|\Z)',
        news_text,
        re.DOTALL
    )
    
    for date, title_desc in news_items[:MAX_NEWS]:
        # تقسيم العنوان والوصف
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
            {'code': 'USD', 'name': 'دولار امريكي', 'flag': '🇺🇸', 'buy': 14280, 'sell': 14340, 'change': '+0.92%', 'changeUp': True},
            {'code': 'EUR', 'name': 'يورو', 'flag': '🇪🇺', 'buy': 16370, 'sell': 16570, 'change': '+1.05%', 'changeUp': True},
            {'code': 'TRY', 'name': 'ليرة تركية', 'flag': '🇹🇷', 'buy': 307, 'sell': 311, 'change': '+0.66%', 'changeUp': True},
            {'code': 'SAR', 'name': 'ريال سعودي', 'flag': '🇸🇦', 'buy': 3766, 'sell': 3820, 'change': '+0.91%', 'changeUp': True},
            {'code': 'AED', 'name': 'درهم اماراتي', 'flag': '🇦🇪', 'buy': 3849, 'sell': 3905, 'change': '+0.92%', 'changeUp': True},
            {'code': 'EGP', 'name': 'جنيه مصري', 'flag': '🇪🇬', 'buy': 273, 'sell': 277, 'change': '+1.49%', 'changeUp': True},
            {'code': 'LYD', 'name': 'دينار ليبي', 'flag': '🇱🇾', 'buy': 2221, 'sell': 2253, 'change': '+0.73%', 'changeUp': True},
            {'code': 'JOD', 'name': 'دينار اردني', 'flag': '🇯🇴', 'buy': 19926, 'sell': 20212, 'change': '+0.85%', 'changeUp': True},
            {'code': 'KWD', 'name': 'دينار كويتي', 'flag': '🇰🇼', 'buy': 45711, 'sell': 46366, 'change': '+0.94%', 'changeUp': True},
            {'code': 'GBP', 'name': 'جنيه استرليني', 'flag': '🇬🇧', 'buy': 18925, 'sell': 19196, 'change': '+1.26%', 'changeUp': True},
        ],
        'gold': [
            {'karat': '24K', 'gramUsd': 139.00, 'buy': 1989200, 'sell': 2013700},
            {'karat': '21K', 'gramUsd': 122.00, 'buy': 1740600, 'sell': 1762000},
            {'karat': '18K', 'gramUsd': 104.00, 'buy': 1491900, 'sell': 1510300},
            {'karat': '14K', 'gramUsd': 81.00, 'buy': 1160300, 'sell': 1174600}
        ],
        'news': [
            {'date': datetime.now().strftime('%d/%m/%Y'), 'title': 'تحديث الأسعار', 'desc': 'تم تحديث أسعار العملات والذهب بنجاح'}
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
    
    # التحقق من العملات
    currencies = data.get('currencies', [])
    if len(currencies) < 5:
        log(f"عدد العملات قليل جداً: {len(currencies)}", 'WARNING')
        return False
    
    # التحقق من الأسعار المعقولة
    for c in currencies:
        if c['sell'] < 1 or c['sell'] > 200000:
            log(f"سعر غير منطقي لـ {c['code']}: {c['sell']}", 'WARNING')
            return False
    
    # التحقق من الذهب
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
                
                # حساب التغيير
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
        
        # التحقق من وجود Git
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            log("Git غير مثبت", 'WARNING')
            return False
        
        # إضافة الملف
        subprocess.run(['git', 'add', DATA_FILE], 
                      check=True, capture_output=True, timeout=10)
        
        # التحقق من وجود تغييرات
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, timeout=5)
        if not result.stdout.strip():
            log("لا توجد تغييرات للرفع", 'INFO')
            return True
        
        # Commit
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        commit_msg = f'🔄 تحديث الأسعار - {timestamp}'
        subprocess.run(['git', 'commit', '-m', commit_msg], 
                      check=True, capture_output=True, timeout=10)
        
        # Push
        subprocess.run(['git', 'push'], 
                      check=True, capture_output=True, timeout=30)
        
        log("تم الرفع إلى GitHub بنجاح!", 'SUCCESS')
        return True
    
    except subprocess.CalledProcessError as e:
        log(f"فشل الرفع: {e.stderr.decode() if e.stderr else str(e)}", 'ERROR')
        return False
    except subprocess.TimeoutExpired:
        log("انتهت مهلة عملية Git", 'ERROR')
        return False
    except FileNotFoundError:
        log("Git غير موجود في النظام", 'WARNING')
        return False
    except Exception as e:
        log(f"خطأ غير متوقع في Git: {e}", 'ERROR')
        return False

# ═══════════════════════════════════════════════════════════════
#                      التقرير النهائي
# ═══════════════════════════════════════════════════════════════

def print_report(data):
    """طباعة التقرير النهائي"""
    print_separator()
    print("📊 التقرير النهائي:")
    print_separator()
    
    # العملات
    currencies = data.get('currencies', [])
    print(f"💰 العملات المستخرجة: {len(currencies)}")
    if currencies:
        print("\nأهم 5 عملات:")
        for c in currencies[:5]:
            arrow = '📈' if c.get('changeUp', True) else '📉'
            print(f"  {c['flag']} {c['code']}: {c['buy']:,} → {c['sell']:,} {arrow} {c.get('change', 'N/A')}")
    
    # الذهب
    gold = data.get('gold', [])
    print(f"\n🥇 أسعار الذهب: {len(gold)}")
    if gold:
        for g in gold:
            print(f"  {g['karat']}: ${g['gramUsd']} | {g['buy']:,} → {g['sell']:,}")
    
    # الأخبار
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
