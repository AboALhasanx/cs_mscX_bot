"""
ثوابت المواد والفصول
"""

SUBJECTS = {
    'ai': {
        'name_ar': 'الذكاء الاصطناعي',
        'name_en': 'Artificial Intelligence',
        'emoji': '🤖',
        'chapters': {
            'ch1': 'الفصل 1: Definitions',
            'ch2': 'الفصل 2: Propositional & Predicate Logic',
            'ch3': 'الفصل 3: Search Algorithms',
            'ch4': 'الفصل 4: Heuristic Search'
        }
    },
    'networks': {
        'name_ar': 'شبكات الحاسوب',
        'name_en': 'Computer Networks',
        'emoji': '📡',
        'chapters': {
            'ch1': 'الفصل 1: Network Fundamentals',
            'ch2': 'الفصل 2: OSI & TCP/IP',
            'ch10': 'الفصل 10: Error Detection'
        }
    },
    'oop': {
        'name_ar': 'البرمجة كائنية التوجه',
        'name_en': 'Object-Oriented Programming',
        'emoji': '👨‍💻',
        'chapters': {
            'ch5': 'الفصل 5: Classes',
            'ch8': 'الفصل 8: Inheritance',
            'ch9': 'الفصل 9: Polymorphism'
        }
    },
    'se': {
        'name_ar': 'هندسة البرمجيات',
        'name_en': 'Software Engineering',
        'emoji': '🛠',
        'chapters': {
            'ch1': 'الفصل 1: Introduction',
            'ch2': 'الفصل 2: Software Processes',
            'ch7': 'الفصل 7: Design & Implementation'
        }
    },
    'ds_algo': {
        'name_ar': 'هياكل البيانات والخوارزميات',
        'name_en': 'Data Structures & Algorithms',
        'emoji': '📊',
        'chapters': {
            'ch3': 'الفصل 3: Arrays & Linked Lists',
            'ch5': 'الفصل 5: Stacks & Queues',
            'ch7': 'الفصل 7: Trees'
        }
    },
    'os': {
        'name_ar': 'نظم التشغيل',
        'name_en': 'Operating Systems',
        'emoji': '⚙️',
        'chapters': {
            'ch3': 'الفصل 3: Processes',
            'ch5': 'الفصل 5: CPU Scheduling',
            'ch6': 'الفصل 6: Synchronization'
        }
    }
}

def get_subject_name(subject_key: str) -> str:
    """الحصول على اسم المادة بالعربية"""
    return SUBJECTS.get(subject_key, {}).get('name_ar', 'غير معروف')

def get_subject_emoji(subject_key: str) -> str:
    """الحصول على emoji المادة"""
    return SUBJECTS.get(subject_key, {}).get('emoji', '📚')

def get_chapter_name(subject_key: str, chapter_key: str) -> str:
    """الحصول على اسم الفصل"""
    subject = SUBJECTS.get(subject_key, {})
    chapters = subject.get('chapters', {})
    return chapters.get(chapter_key, 'غير معروف')
