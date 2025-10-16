"""
خدمة إدارة الأسئلة
تدعم التحميل من GitHub أو الملفات المحلية + metadata
"""

import json
import random
import requests
import re
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class QuestionService:
    """خدمة إدارة الأسئلة مع دعم GitHub و metadata"""
    
    def __init__(self, questions_dir: str, github_url: str = None, 
                 use_online: bool = False, cache_enabled: bool = True,
                 cache_duration: int = 60):
        """
        تهيئة خدمة الأسئلة
        
        Args:
            questions_dir: مسار المجلد المحلي
            github_url: رابط GitHub Raw
            use_online: استخدام GitHub أم الملفات المحلية
            cache_enabled: تفعيل الـ Cache
            cache_duration: مدة الـ Cache بالدقائق
        """
        self.questions_dir = Path(questions_dir)
        self.github_url = github_url
        self.use_online = use_online
        self.cache_enabled = cache_enabled
        self.cache_duration = timedelta(minutes=cache_duration)
        
        # مخزن الـ Cache في الذاكرة
        self._cache = {}
        self._cache_timestamps = {}
    
    def _is_cache_valid(self, key: str) -> bool:
        """التحقق من صلاحية الـ Cache"""
        if not self.cache_enabled:
            return False
        
        if key not in self._cache_timestamps:
            return False
        
        elapsed = datetime.now() - self._cache_timestamps[key]
        return elapsed < self.cache_duration
    
    def _get_from_cache(self, key: str):
        """الحصول على البيانات من الـ Cache"""
        if self._is_cache_valid(key):
            logger.info(f"📦 تحميل من Cache: {key}")
            return self._cache.get(key)
        return None
    
    def _save_to_cache(self, key: str, data):
        """حفظ البيانات في الـ Cache"""
        if self.cache_enabled:
            self._cache[key] = data
            self._cache_timestamps[key] = datetime.now()
            logger.info(f"💾 حفظ في Cache: {key}")
    
    def load_questions_from_github(self, filepath: str) -> dict:
        """
        تحميل الأسئلة من GitHub مع دعم metadata
        
        Args:
            filepath: المسار النسبي في الريبو
        
        Returns:
            dict: {'metadata': {...}, 'questions': [...]}
        """
        # التحقق من الـ Cache
        cached = self._get_from_cache(filepath)
        if cached:
            return cached
        
        url = f"{self.github_url}/{filepath}"
        
        try:
            logger.info(f"🌐 تحميل من GitHub: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # دعم الصيغتين: الجديدة (مع metadata) والقديمة (مصفوفة مباشرة)
            if isinstance(data, dict) and 'questions' in data:
                # صيغة جديدة مع metadata
                result = data
                logger.info(f"✅ تم تحميل {len(result['questions'])} سؤال مع metadata")
            elif isinstance(data, list):
                # صيغة قديمة (مصفوفة مباشرة)
                result = {
                    'metadata': {
                        'title': 'Unknown',
                        'title_ar': 'غير معروف',
                        'description': '',
                        'difficulty': 'medium'
                    },
                    'questions': data
                }
                logger.info(f"✅ تم تحميل {len(data)} سؤال (صيغة قديمة)")
            else:
                raise ValueError("الملف يجب أن يكون مصفوفة أو object مع حقل 'questions'")
            
            # حفظ في الـ Cache
            self._save_to_cache(filepath, result)
            
            return result
        
        except requests.RequestException as e:
            logger.error(f"❌ فشل التحميل من GitHub: {e}")
            raise ConnectionError(f"فشل الاتصال بـ GitHub: {str(e)}")
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ خطأ في JSON من GitHub: {e}")
            raise ValueError(f"ملف JSON غير صالح: {str(e)}")
    
    def load_questions_from_local(self, filename: str) -> dict:
        """
        تحميل الأسئلة من ملف محلي
        
        Args:
            filename: اسم الملف (مثل 'ai/ch1.json')
        
        Returns:
            dict: {'metadata': {...}, 'questions': [...]}
        """
        filepath = self.questions_dir / filename
        
        if not filepath.exists():
            logger.error(f"❌ الملف غير موجود: {filepath}")
            raise FileNotFoundError(f"الملف غير موجود: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # دعم الصيغتين
            if isinstance(data, dict) and 'questions' in data:
                result = data
                logger.info(f"✅ تم تحميل {len(result['questions'])} سؤال مع metadata من الملف المحلي")
            elif isinstance(data, list):
                result = {
                    'metadata': {
                        'title': 'Unknown',
                        'title_ar': 'غير معروف'
                    },
                    'questions': data
                }
                logger.info(f"✅ تم تحميل {len(data)} سؤال (صيغة قديمة) من الملف المحلي")
            else:
                raise ValueError("الملف يجب أن يكون مصفوفة أو object مع حقل 'questions'")
            
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ خطأ في JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ خطأ في التحميل: {e}")
            raise
    
    def get_available_parts_from_github(self, subject: str, folder_name: str) -> list:
        """
        اكتشاف جميع الملفات المتاحة في مجلد المادة على GitHub
        + تحميل metadata لكل ملف للحصول على العناوين
        
        Args:
            subject: مفتاح المادة (مثل 'ai')
            folder_name: اسم المجلد على GitHub (مثل 'ai_quizzes')
        
        Returns:
            قائمة بالأجزاء مع عناوينها من metadata
        """
        try:
            # GitHub API للحصول على قائمة الملفات في المجلد
            api_url = f"https://api.github.com/repos/AboALhasanx/json-files/contents/{folder_name}"
            
            logger.info(f"🔍 البحث عن الملفات في: {folder_name}")
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            files_data = response.json()
            
            # فلترة ملفات JSON فقط
            parts = []
            for file_info in files_data:
                if file_info['name'].endswith('.json'):
                    filename = file_info['name']
                    
                    # استخراج رقم الجزء من اسم الملف
                    match = re.search(r'_pt(\d+)\.json$', filename)
                    if match:
                        part_num = match.group(1)
                        filepath = f'{folder_name}/{filename}'
                        
                        # محاولة تحميل metadata للحصول على العنوان
                        try:
                            part_data = self.load_questions_from_github(filepath)
                            metadata = part_data.get('metadata', {})
                            title_ar = metadata.get('title_ar', f'الجزء {part_num}')
                            title_en = metadata.get('title', f'Part {part_num}')
                        except Exception as e:
                            logger.warning(f"⚠️ فشل تحميل metadata من {filename}: {e}")
                            title_ar = f'الجزء {part_num}'
                            title_en = f'Part {part_num}'
                        
                        parts.append({
                            'part': f'pt{part_num}',
                            'file': filename,
                            'filepath': filepath,
                            'display': f'الجزء {part_num}',  # fallback
                            'title_ar': title_ar,  # العنوان الحقيقي من metadata
                            'title_en': title_en,
                            'part_num': int(part_num)
                        })
            
            # ترتيب حسب رقم الجزء
            parts.sort(key=lambda x: x['part_num'])
            
            logger.info(f"✅ تم العثور على {len(parts)} جزء في {folder_name}")
            return parts
        
        except requests.RequestException as e:
            logger.error(f"❌ فشل الاتصال بـ GitHub API: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ خطأ في اكتشاف الملفات: {e}")
            return []
    
    def load_questions_for_part(self, subject: str, part_filepath: str) -> dict:
        """
        تحميل الأسئلة لجزء محدد من مادة
        
        Args:
            subject: مفتاح المادة (مثل 'ai')
            part_filepath: المسار الكامل للملف على GitHub
        
        Returns:
            dict: {'metadata': {...}, 'questions': [...]}
        """
        if self.use_online and self.github_url:
            # التحميل من GitHub
            try:
                return self.load_questions_from_github(part_filepath)
            
            except (ConnectionError, ValueError) as e:
                logger.warning(f"⚠️ فشل التحميل من GitHub: {e}")
                raise
        
        else:
            # التحميل من الملفات المحلية
            local_path = f"{subject}/{part_filepath.split('/')[-1]}"
            return self.load_questions_from_local(local_path)
    
    def get_random_questions(self, questions: list, count: int) -> list:
        """اختيار أسئلة عشوائية"""
        actual_count = min(len(questions), count)
        
        if actual_count < count:
            logger.warning(f"⚠️ عدد الأسئلة المتاحة ({len(questions)}) أقل من المطلوب ({count})")
        
        return random.sample(questions, actual_count)
    
    def validate_question(self, question: dict) -> bool:
        """التحقق من صحة بنية السؤال"""
        required_fields = ['question', 'options', 'correct_option_id']
        
        for field in required_fields:
            if field not in question:
                logger.error(f"❌ حقل مفقود: {field}")
                return False
        
        # التحقق من طول السؤال
        if len(question['question']) > 300:
            logger.error(f"❌ السؤال طويل جداً ({len(question['question'])} حرف)")
            return False
        
        # التحقق من عدد الخيارات
        if len(question['options']) < 2 or len(question['options']) > 10:
            logger.error("❌ يجب أن يحتوي السؤال على 2-10 خيارات")
            return False
        
        # التحقق من طول كل خيار
        for i, option in enumerate(question['options']):
            if len(option) > 100:
                logger.error(f"❌ الخيار {i+1} طويل جداً ({len(option)} حرف): {option[:50]}...")
                return False
        
        # التحقق من صحة رقم الإجابة
        if not (0 <= question['correct_option_id'] < len(question['options'])):
            logger.error("❌ رقم الإجابة الصحيحة خارج النطاق")
            return False
        
        return True
    
    def shuffle_question_options(self, question: dict) -> dict:
        """
        خلط خيارات السؤال بشكل عشوائي
        مع تحديث correct_option_id ليشير للخيار الصحيح الجديد
        
        Args:
            question: السؤال الأصلي
        
        Returns:
            dict: السؤال مع خيارات مخلوطة
        """
        import copy
        
        # نسخ عميقة لتجنب تعديل الأصل
        shuffled_q = copy.deepcopy(question)
        
        # الحصول على الإجابة الصحيحة الحالية
        correct_option_text = shuffled_q['options'][shuffled_q['correct_option_id']]
        
        # خلط الخيارات
        random.shuffle(shuffled_q['options'])
        
        # إيجاد الموقع الجديد للإجابة الصحيحة
        new_correct_index = shuffled_q['options'].index(correct_option_text)
        shuffled_q['correct_option_id'] = new_correct_index
        
        return shuffled_q
    
    def shuffle_all_questions(self, questions: list) -> list:
        """
        خلط جميع الأسئلة وخياراتها بشكل عشوائي
        
        Args:
            questions: قائمة الأسئلة الأصلية
        
        Returns:
            list: قائمة مخلوطة مع خيارات مخلوطة
        """
        # خلط ترتيب الأسئلة
        shuffled_questions = random.sample(questions, len(questions))
        
        # خلط خيارات كل سؤال
        for i in range(len(shuffled_questions)):
            shuffled_questions[i] = self.shuffle_question_options(shuffled_questions[i])
        
        logger.info(f"🔀 تم خلط {len(shuffled_questions)} سؤال مع خياراتهم")
        return shuffled_questions


    def clear_cache(self):
        """مسح الـ Cache"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("🗑️ تم مسح Cache")
