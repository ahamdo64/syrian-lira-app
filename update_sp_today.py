#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت تحديث بيانات سعر الليرة السورية
من موقع sp-today.com
المهندس الاستشاري أحمد عمران
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import os

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

        data = {
            'lastUpdate': datetime.now().isoformat(),
            'currencies': [],
            'gold': [],
            'news': []
        }

        # استخراج العملات
        currency_patterns = [
            {'code': 'USD', 'name': 'دولار أمريكي', 'flag': '🇺🇸'},
            {'code': 'EUR', 'name': 'يورو', 'flag': '🇪🇺'},
            {'code': 'TRY', 'name': 'ليرة تركية', 'flag': '🇹🇷'},
            {'code': 'SAR', 'name': 'ريال سعودي', 'flag': '🇸🇦'},
            {'code': 'AED', 'name': 'درهم إماراتي', 'flag': '🇦🇪'},
            {'code': 'EGP', 'name': 'جنيه مصري', 'flag': '🇪🇬'}
        ]

        for pattern in currency_patterns:
            code = pattern['code']
            buy_match = re.search(rf'{code}.*?\b(\d{{1,2}},?\d{{3,}})\b.*?شراء', text, re.IGNORECASE)
            sell_match = re.search(rf'{code}.*?\b(\d{{1,2}},?\d{{3,}})\b.*?مبيع', text, re.IGNORECASE)

            if buy_match or sell_match:
                buy = int(buy_match.group(1).replace(',', '')) if buy_match else 0
                sell = int(sell_match.group(1).replace(',', '')) if sell_match else 0

                if buy > 0 or sell > 0:
                    data['currencies'].append({
                        'code': code,
                        'name': pattern['name'],
                        'flag': pattern['flag'],
                        'buy': buy or sell,
                        'sell': sell or buy,
                        'change': '+0.00%',
                        'changeUp': True
                    })

        # استخراج الذهب
        karats = ['24K', '21K', '18K', '14K']
        for karat in karats:
            match = re.search(rf'{karat}.*?\$?(\d+\.\d+).*?(\d{{1,2}},?\d{{3,}}).*?(\d{{1,2}},?\d{{3,}})', text)
            if match:
                data['gold'].append({
                    'karat': karat,
                    'gramUsd': float(match.group(1)),
                    'buy': int(match.group(2).replace(',', '')),
                    'sell': int(match.group(3).replace(',', ''))
                })

        # استخراج الأخبار
        news_elements = soup.find_all(['article', 'div'], class_=re.compile('news|post|item'))
        for i, el in enumerate(news_elements[:5]):
            title = el.find(['h2', 'h3', 'h4'])
            date = el.find(['time', 'span'], class_=re.compile('date|time'))
            desc = el.find('p')

            data['news'].append({
                'date': date.text.strip() if date else datetime.now().strftime('%d/%m/%Y'),
                'title': title.text.strip() if title else 'خبر اقتصادي',
                'desc': desc.text.strip()[:200] if desc else ''
            })

        print(f"✅ تم استخراج {len(data['currencies'])} عملة")
        print(f"✅ تم استخراج {len(data['gold'])} عيار ذهب")
        print(f"✅ تم استخراج {len(data['news'])} خبر")

        return data

    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None

def save_data(data, filename='sp_today_data.json'):
    """حفظ البيانات في ملف JSON"""
    if data is None:
        print("❌ لا توجد بيانات لحفظها")
        return False

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ تم حفظ البيانات في {filename}")
        print(f"📅 آخر تحديث: {data['lastUpdate']}")
        return True

    except Exception as e:
        print(f"❌ خطأ في الحفظ: {e}")
        return False

def load_default_data():
    """تحميل البيانات الافتراضية"""
    return {
        'lastUpdate': datetime.now().isoformat(),
        'currencies': [
            {'code': 'USD', 'name': 'دولار أمريكي', 'flag': '🇺🇸', 'buy': 14125, 'sell': 14180, 'change': '+0.32%', 'changeUp': True},
            {'code': 'EUR', 'name': 'يورو', 'flag': '🇪🇺', 'buy': 16130, 'sell': 16320, 'change': '+0.19%', 'changeUp': True},
            {'code': 'TRY', 'name': 'ليرة تركية', 'flag': '🇹🇷', 'buy': 304, 'sell': 308, 'change': '+0.00%', 'changeUp': True},
            {'code': 'SAR', 'name': 'ريال سعودي', 'flag': '🇸🇦', 'buy': 3721, 'sell': 3773, 'change': '+0.32%', 'changeUp': True},
            {'code': 'AED', 'name': 'درهم إماراتي', 'flag': '🇦🇪', 'buy': 3808, 'sell': 3861, 'change': '+0.32%', 'changeUp': True},
            {'code': 'EGP', 'name': 'جنيه مصري', 'flag': '🇪🇬', 'buy': 268, 'sell': 272, 'change': '+0.37%', 'changeUp': True}
        ],
        'gold': [
            {'karat': '24K', 'gramUsd': 138.00, 'buy': 1950200, 'sell': 1974400},
            {'karat': '21K', 'gramUsd': 121.00, 'buy': 1706400, 'sell': 1727600},
            {'karat': '18K', 'gramUsd': 104.00, 'buy': 1462600, 'sell': 1480800},
            {'karat': '14K', 'gramUsd': 81.00, 'buy': 1137500, 'sell': 1151700}
        ],
        'news': [
            {'date': '08/06/2026', 'title': 'شركة سعودية تطلق استثماراً سكنياً بملياري دولار قرب دمشق', 'desc': 'أطلقت شركة عقارية سعودية مشروعين سكنيين في ريف دمشق في 7 حزيران 2026 باستثمار يتجاوز ملياري دولار وخطة لنحو 22 ألف وحدة سكنية.'},
            {'date': '08/06/2026', 'title': 'المركزي السوري يتيح لمتلقي الحوالات اختيار عملة الاستلام', 'desc': 'أصدر المصرف المركزي السوري قراراً يسمح لمتلقي الحوالات الواردة من الخارج باختيار عملة الاستلام.'},
            {'date': '07/06/2026', 'title': 'سوريا تطرح قروضاً ميسّرة لتجديد 75% من أسطول الشحن البري المتقادم', 'desc': 'أعلنت الحكومة السورية عن خطة لتجديد أسطول النقل البري من خلال قروض ميسرة.'},
            {'date': '07/06/2026', 'title': 'سوريا تطلق موسم تسويق القمح 2026 بافتتاح مراكز استلام جديدة', 'desc': 'بدأت سوريا موسم تسويق القمح للعام 2026 مع افتتاح مراكز استلام جديدة في مختلف المحافظات.'},
            {'date': '07/06/2026', 'title': 'العراق يستهدف مرفأ بانياس السوري لتصدير نفطه بعيداً عن مضيق هرمز', 'desc': 'تدرس الحكومة العراقية استخدام مرفأ بانياس السوري كمخرج بديل لتصدير النفط.'}
        ]
    }

if __name__ == '__main__':
    print("=" * 50)
    print("🔄 سكربت تحديث بيانات سعر الليرة السورية")
    print("👨‍💼 المهندس الاستشاري أحمد عمران")
    print("=" * 50)

    # محاولة جلب البيانات
    data = fetch_data()

    if data is None or not data['currencies']:
        print("⚠️ فشل الاتصال بالموقع، استخدام البيانات الافتراضية...")
        data = load_default_data()

    # حفظ البيانات
    save_data(data)

    print("=" * 50)
    print("✅ تم الانتهاء!")
    print("📁 الملف: sp_today_data.json")
    print("=" * 50)
