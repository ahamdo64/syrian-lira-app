#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت تحديث بيانات سعر الليرة السورية
من موقع sp-today.com
المهندس الاستشاري احمد عمران
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import sys

def fetch_data():
    """جلب البيانات من الموقع"""
    url = 'https://sp-today.com/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ar,en;q=0.9',
    }

    try:
        print("🔍 جاري الاتصال بـ sp-today.com...")
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"❌ خطأ: Status code {response.status_code}")
            return None

        print("✅ تم الاتصال بنجاح!")

        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        # طباعة جزء من النص للتصحيح
        print("\n📄 عينة من النص المستخرج:")
        print(text[:1000])
        print("...")

        data = {
            'lastUpdate': datetime.now().isoformat(),
            'currencies': [],
            'gold': [],
            'news': []
        }

        # ===== استخراج العملات =====
        print("\n💰 جاري استخراج اسعار العملات...")

        # البحث عن جدول العملات
        currency_section = text.find('الأسعار الحالية')
        if currency_section != -1:
            currency_text = text[currency_section:currency_section + 3000]

            # أنماط البحث المحدثة
            currency_patterns = [
                {'code': 'USD', 'name': 'دولار امريكي', 'flag': '🇺🇸'},
                {'code': 'EUR', 'name': 'يورو', 'flag': '🇪🇺'},
                {'code': 'TRY', 'name': 'ليرة تركية', 'flag': '🇹🇷'},
                {'code': 'SAR', 'name': 'ريال سعودي', 'flag': '🇸🇦'},
                {'code': 'AED', 'name': 'درهم اماراتي', 'flag': '🇦🇪'},
                {'code': 'EGP', 'name': 'جنيه مصري', 'flag': '🇪🇬'}
            ]

            for pattern in currency_patterns:
                code = pattern['code']

                # البحث عن النمط: USD ... رقم ... رقم ... %
                # مثال: USDدولار أمريكي14,28014,340+0.92%
                pattern_regex = rf'{code}.*?([0-9,]{{3,}}).*?([0-9,]{{3,}}).*?([+-]?[0-9.]+)%'
                match = re.search(pattern_regex, currency_text, re.DOTALL)

                if match:
                    buy_str = match.group(1).replace(',', '')
                    sell_str = match.group(2).replace(',', '')
                    change_str = match.group(3)

                    try:
                        buy = int(buy_str)
                        sell = int(sell_str)
                        change = f"{change_str}%"
                        change_up = not change_str.startswith('-')

                        data['currencies'].append({
                            'code': code,
                            'name': pattern['name'],
                            'flag': pattern['flag'],
                            'buy': buy,
                            'sell': sell,
                            'change': change,
                            'changeUp': change_up
                        })
                        print(f"  ✅ {code}: شراء {buy:,} - مبيع {sell:,} - {change}")
                    except ValueError:
                        print(f"  ⚠️ خطأ في تحويل ارقام {code}")
                else:
                    print(f"  ❌ لم يتم العثور على {code}")

        # ===== استخراج الذهب =====
        print("\n🥇 جاري استخراج اسعار الذهب...")

        gold_section = text.find('أسعار الذهب')
        if gold_section != -1:
            gold_text = text[gold_section:gold_section + 2000]

            karats = ['24K', '21K', '18K', '14K']
            for karat in karats:
                # البحث عن: 24K ... $رقم ... رقم ... رقم
                pattern = rf'{karat}.*?\$?([0-9.]+).*?([0-9,]{{3,}}).*?([0-9,]{{3,}})'
                match = re.search(pattern, gold_text, re.DOTALL)

                if match:
                    try:
                        gram_usd = float(match.group(1))
                        buy = int(match.group(2).replace(',', ''))
                        sell = int(match.group(3).replace(',', ''))

                        data['gold'].append({
                            'karat': karat,
                            'gramUsd': gram_usd,
                            'buy': buy,
                            'sell': sell
                        })
                        print(f"  ✅ {karat}: ${gram_usd} - شراء {buy:,} - مبيع {sell:,}")
                    except ValueError:
                        print(f"  ⚠️ خطأ في تحويل ارقام {karat}")
                else:
                    print(f"  ❌ لم يتم العثور على {karat}")

        # ===== استخراج الاخبار =====
        print("\n📰 جاري استخراج الاخبار...")

        news_section = text.find('أخبار اقتصادية')
        if news_section != -1:
            news_text = text[news_section:news_section + 3000]

            # تقسيم الاخبار
            news_items = re.findall(r'(\d{2}‏/\d{2}‏/\d{4}[^
]*?)\*\*([^
]+?)\*\*([^
]*?)(?=\d{2}‏/\d{2}‏/\d{4}|$)', news_text, re.DOTALL)

            for i, (date, title, desc) in enumerate(news_items[:5]):
                data['news'].append({
                    'date': date.strip().replace('‏', ''),
                    'title': title.strip(),
                    'desc': desc.strip()[:200]
                })
                print(f"  ✅ خبر {i+1}: {title.strip()[:50]}...")

        print(f"\n📊 النتائج:")
        print(f"  💰 العملات: {len(data['currencies'])}")
        print(f"  🥇 الذهب: {len(data['gold'])}")
        print(f"  📰 الاخبار: {len(data['news'])}")

        return data

    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_default_data():
    """تحميل البيانات الافتراضية"""
    return {
        'lastUpdate': datetime.now().isoformat(),
        'currencies': [
            {'code': 'USD', 'name': 'دولار امريكي', 'flag': '🇺🇸', 'buy': 14280, 'sell': 14340, 'change': '+0.92%', 'changeUp': True},
            {'code': 'EUR', 'name': 'يورو', 'flag': '🇪🇺', 'buy': 16370, 'sell': 16570, 'change': '+1.05%', 'changeUp': True},
            {'code': 'TRY', 'name': 'ليرة تركية', 'flag': '🇹🇷', 'buy': 307, 'sell': 311, 'change': '+0.66%', 'changeUp': True},
            {'code': 'SAR', 'name': 'ريال سعودي', 'flag': '🇸🇦', 'buy': 3766, 'sell': 3820, 'change': '+0.91%', 'changeUp': True},
            {'code': 'AED', 'name': 'درهم اماراتي', 'flag': '🇦🇪', 'buy': 3849, 'sell': 3905, 'change': '+0.92%', 'changeUp': True},
            {'code': 'EGP', 'name': 'جنيه مصري', 'flag': '🇪🇬', 'buy': 273, 'sell': 277, 'change': '+1.49%', 'changeUp': True}
        ],
        'gold': [
            {'karat': '24K', 'gramUsd': 139.00, 'buy': 1989200, 'sell': 2013700},
            {'karat': '21K', 'gramUsd': 122.00, 'buy': 1740600, 'sell': 1762000},
            {'karat': '18K', 'gramUsd': 104.00, 'buy': 1491900, 'sell': 1510300},
            {'karat': '14K', 'gramUsd': 81.00, 'buy': 1160300, 'sell': 1174600}
        ],
        'news': [
            {'date': '08/06/2026', 'title': 'خطة بـ37 مليون دولار لإعادة تأهيل طرق وجسور دير الزور', 'desc': 'كشفت الجهات الرسمية عن خطة بقيمة تتجاوز 37 مليون دولار لإعادة تأهيل الطرق والجسور المتضررة من الحرب والفيضانات في دير الزور.'},
            {'date': '08/06/2026', 'title': 'تعليق مطار دمشق وتحويل رحلات سورية مع إغلاق الممرات الجوية الجنوبية', 'desc': ''},
            {'date': '08/06/2026', 'title': 'شركة سعودية تطلق استثماراً سكنياً بملياري دولار قرب دمشق', 'desc': 'أطلقت شركة عقارية سعودية مشروعين سكنيين في ريف دمشق في 7 حزيران 2026 باستثمار يتجاوز ملياري دولار.'},
            {'date': '08/06/2026', 'title': 'المركزي السوري يتيح لمتلقي الحوالات اختيار عملة الاستلام', 'desc': 'أصدر المصرف المركزي السوري قراراً يسمح لمتلقي الحوالات الواردة من الخارج باختيار عملة الاستلام.'},
            {'date': '07/06/2026', 'title': 'سوريا تطرح قروضاً ميسّرة لتجديد 75% من أسطول الشحن البري المتقادم', 'desc': 'أعلنت الحكومة السورية عن خطة لتجديد أسطول النقل البري من خلال قروض ميسرة.'}
        ]
    }

def save_data(data, filename='sp_today_data.json'):
    """حفظ البيانات في ملف JSON"""
    if data is None:
        print("❌ لا توجد بيانات لحفظها")
        return False

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ تم حفظ البيانات في {filename}")
        print(f"📅 اخر تحديث: {data['lastUpdate']}")
        return True

    except Exception as e:
        print(f"❌ خطأ في الحفظ: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🔄 سكربت تحديث بيانات سعر الليرة السورية")
    print("👨‍💼 المهندس الاستشاري احمد عمران")
    print("=" * 60)

    # محاولة جلب البيانات
    data = fetch_data()

    # اذا فشل الاتصال أو لم يتم استخراج بيانات، استخدم الافتراضية
    if data is None or len(data['currencies']) == 0:
        print("\n⚠️ فشل الاتصال أو لم يتم استخراج بيانات، استخدام البيانات الافتراضية...")
        data = load_default_data()
        print("✅ تم تحميل البيانات الافتراضية")

    # حفظ البيانات
    save_data(data)

    print("=" * 60)
    print("✅ تم الانتهاء!")
    print("📁 الملف: sp_today_data.json")
    print("=" * 60)
