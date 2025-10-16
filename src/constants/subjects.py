"""
ثوابت المواد - نسخة محدثة مع تفاصيل كاملة
"""

SUBJECTS = {
    'ai': {
        'name_ar': 'الذكاء الاصطناعي',
        'name_en': 'Artificial Intelligence',
        'name_short': 'AI',
        'emoji': '🤖',
        'description': 'مفاهيم الذكاء الاصطناعي والخوارزميات الذكية'
    },
    'networks': {
        'name_ar': 'شبكات الحاسوب',
        'name_en': 'Computer Networks',
        'name_short': 'Networks',
        'emoji': '📡',
        'description': 'بروتوكولات الشبكات والاتصالات'
    },
    'oop': {
        'name_ar': 'البرمجة كائنية التوجه',
        'name_en': 'Object-Oriented Programming',
        'name_short': 'OOP',
        'emoji': '👨‍💻',
        'description': 'مفاهيم OOP والتصميم الكائني'
    },
    'se': {
        'name_ar': 'هندسة البرمجيات',
        'name_en': 'Software Engineering',
        'name_short': 'SE',
        'emoji': '🛠',
        'description': 'دورة حياة البرمجيات والتصميم'
    },
    'ds_algo': {
        'name_ar': 'هياكل البيانات والخوارزميات',
        'name_en': 'Data Structures & Algorithms',
        'name_short': 'DS & Algo',
        'emoji': '📊',
        'description': 'هياكل البيانات الأساسية والمتقدمة'
    },
    'os': {
        'name_ar': 'نظم التشغيل',
        'name_en': 'Operating Systems',
        'name_short': 'OS',
        'emoji': '⚙️',
        'description': 'مفاهيم نظم التشغيل والجدولة'
    }
}

def get_subject_name(subject_key: str) -> str:
    """الحصول على اسم المادة بالعربية"""
    return SUBJECTS.get(subject_key, {}).get('name_ar', 'غير معروف')

def get_subject_emoji(subject_key: str) -> str:
    """الحصول على emoji المادة"""
    return SUBJECTS.get(subject_key, {}).get('emoji', '📚')

def get_subject_name_en(subject_key: str) -> str:
    """الحصول على اسم المادة بالإنجليزية"""
    return SUBJECTS.get(subject_key, {}).get('name_en', 'Unknown')

def get_subject_short(subject_key: str) -> str:
    """الحصول على الاسم المختصر"""
    return SUBJECTS.get(subject_key, {}).get('name_short', subject_key.upper())

def get_subject_full_name(subject_key: str) -> str:
    """الحصول على الاسم الكامل (عربي + إنجليزي)"""
    subject = SUBJECTS.get(subject_key, {})
    name_ar = subject.get('name_ar', 'غير معروف')
    name_en = subject.get('name_en', 'Unknown')
    emoji = subject.get('emoji', '📚')
    return f"{emoji} {name_ar} ({name_en})"
