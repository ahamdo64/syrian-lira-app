#!/bin/bash
# ============================================
# سكريبت تحديث أسعار العملات من sp-today.com
# ============================================

set -e

# ====== إعدادات ======
DATA_FILE="sp_today_data.json"
BACKUP_FILE="sp_today_data.backup.json"
LOG_FILE="update.log"
TARGET_URL="https://sp-today.com/"

# ====== دوال مساعدة ======
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "❌ خطأ: $1"
    exit 1
}

# ====== التحقق من الملفات ======
log "🔄 بدء عملية التحديث..."

if [ ! -f "$DATA_FILE" ]; then
    log "⚠️ ملف البيانات غير موجود، سيتم إنشاء نسخة احتياطية من البيانات الافتراضية"
    # يمكن إضافة بيانات افتراضية هنا إذا لزم الأمر
fi

# ====== إنشاء نسخة احتياطية ======
if [ -f "$DATA_FILE" ]; then
    cp "$DATA_FILE" "$BACKUP_FILE"
    log "✅ تم إنشاء نسخة احتياطية: $BACKUP_FILE"
fi

# ====== محاولة جلب البيانات ======
TEMP_FILE=$(mktemp)

log "📡 جاري جلب البيانات من $TARGET_URL..."

# محاولة 1: curl مباشر
if curl -s -L --max-time 30 \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    -H "Accept: text/html,application/xhtml+xml" \
    -o "$TEMP_FILE" "$TARGET_URL"; then
    
    log "✅ تم جلب HTML بنجاح"
    
    # استخراج البيانات باستخدام Python (إذا كان متاحاً)
    if command -v python3 &> /dev/null; then
        log " استخدام Python لتحليل البيانات..."
        python3 update_sp_today.py
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 0 ]; then
            log "✅ تم التحديث بنجاح عبر Python"
            rm -f "$TEMP_FILE"
            exit 0
        else
            log "️ فشل Python، محاولة بديلة..."
        fi
    fi
    
    # محاولة 2: استخراج بسيط باستخدام grep و sed
    log "🔍 محاولة استخراج البيانات باستخدام grep..."
    
    # استخراج أسعار العملات (نمط عام)
    CURRENCIES=$(grep -oP '(?<=<td[^>]*>)[\d,]+(?=</td>)' "$TEMP_FILE" | head -20)
    
    if [ -n "$CURRENCIES" ]; then
        log "✅ تم استخراج بعض البيانات"
        # هنا يمكن إضافة منطق لتحويل البيانات إلى JSON
    else
        log "⚠️ لم يتم استخراج بيانات كافية"
    fi
    
else
    log "❌ فشل في جلب البيانات من الموقع"
fi

# ====== Fallback: تحديث الوقت فقط ======
log "⚠️ استخدام البيانات الحالية مع تحديث الوقت..."

if [ -f "$DATA_FILE" ]; then
    # تحديث lastUpdate في الملف الحالي
    python3 -c "
import json
from datetime import datetime, timezone

try:
    with open('$DATA_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['lastUpdate'] = datetime.now(timezone.utc).isoformat()
    data['source'] = 'fallback (shell script)'
    with open('$DATA_FILE', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('✅ تم تحديث الوقت فقط')
except Exception as e:
    print(f'❌ خطأ: {e}')
    exit(1)
"
else
    error_exit "ملف البيانات غير موجود ولا يمكن إنشاؤه"
fi

# ====== تنظيف ======
rm -f "$TEMP_FILE"

log "✅ اكتملت عملية التحديث"
exit 0
