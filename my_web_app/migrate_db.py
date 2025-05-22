#!/usr/bin/env python3
"""
Database migration script to add language support
Run this script to update your existing database with the new language features
"""

import sys
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def migrate_database():
    """Migrate the database to add language support"""
    
    # Database configuration
    DATABASE_URL = 'sqlite:///app.db'
    engine = create_engine(DATABASE_URL)
    
    try:
        print("Starting database migration...")
        
        # Check if user table exists and add language column if missing
        inspector = inspect(engine)
        
        if 'user' in inspector.get_table_names():
            columns = [column['name'] for column in inspector.get_columns('user')]
            
            if 'language' not in columns:
                print("Adding language column to user table...")
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE user ADD COLUMN language VARCHAR(10) DEFAULT 'en'"))
                    conn.commit()
                print("✓ Language column added to user table")
            else:
                print("✓ Language column already exists in user table")
        else:
            print("⚠ User table not found - will be created when app runs")
        
        # Create Label table if it doesn't exist
        if 'label' not in inspector.get_table_names():
            print("Creating label table...")
            create_label_table_sql = """
            CREATE TABLE label (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(100) UNIQUE NOT NULL,
                en TEXT,
                ar TEXT,
                ru TEXT,
                zh TEXT,
                es TEXT,
                tg TEXT,
                fa TEXT,
                kk TEXT,
                az TEXT
            )
            """
            with engine.connect() as conn:
                conn.execute(text(create_label_table_sql))
                conn.commit()
            print("✓ Label table created")
            
            # Add initial labels
            print("Adding initial labels...")
            initial_labels = [
                ('app_title', 'Cybersecurity Maturity Assessment', 'تقييم نضج الأمن السيبراني'),
                ('login', 'Login', 'تسجيل الدخول'),
                ('username', 'Username', 'اسم المستخدم'),
                ('password', 'Password', 'كلمة المرور'),
                ('submit', 'Submit', 'إرسال'),
                ('cancel', 'Cancel', 'إلغاء'),
                ('welcome', 'Welcome', 'مرحباً'),
                ('logout', 'Logout', 'تسجيل الخروج'),
                ('dashboard', 'Dashboard', 'لوحة التحكم'),
                ('admin', 'Admin', 'الإدارة'),
                ('manage_labels', 'Manage Labels', 'إدارة التسميات'),
                ('add_new_label', 'Add New Label', 'إضافة تسمية جديدة'),
                ('edit_label', 'Edit Label', 'تعديل التسمية'),
                ('delete_label', 'Delete Label', 'حذف التسمية'),
                ('save', 'Save', 'حفظ'),
                ('back', 'Back', 'رجوع'),
                ('key', 'Key', 'المفتاح'),
                ('english', 'English', 'الإنجليزية'),
                ('arabic', 'Arabic', 'العربية'),
                ('russian', 'Russian', 'الروسية'),
                ('chinese', 'Chinese', 'الصينية'),
                ('spanish', 'Spanish', 'الإسبانية'),
                ('tajik', 'Tajik', 'التاجيكية'),
                ('farsi', 'Farsi', 'الفارسية'),
                ('kazakh', 'Kazakh', 'الكازاخية'),
                ('azerbaijani', 'Azerbaijani', 'الأذربيجانية'),
                ('actions', 'Actions', 'الإجراءات'),
                ('edit', 'Edit', 'تعديل'),
                ('delete', 'Delete', 'حذف'),
                ('confirm_delete', 'Are you sure you want to delete this label?', 'هل أنت متأكد من حذف هذه التسمية؟'),
                ('access_denied', 'Access denied', 'تم رفض الوصول'),
                ('invalid_credentials', 'Invalid username or password', 'اسم المستخدم أو كلمة المرور غير صحيحة'),
                ('label_key_exists', 'Label key already exists', 'مفتاح التسمية موجود بالفعل'),
                ('label_added_successfully', 'Label added successfully', 'تم إضافة التسمية بنجاح'),
                ('label_updated_successfully', 'Label updated successfully', 'تم تحديث التسمية بنجاح'),
                ('label_deleted_successfully', 'Label deleted successfully', 'تم حذف التسمية بنجاح'),
                ('no_labels_found', 'No labels found', 'لم يتم العثور على تسميات'),
                ('add_first_label', 'Add Your First Label', 'أضف أول تسمية'),
                ('key_description', 'Unique identifier for this label (e.g., login_button)', 'معرف فريد لهذه التسمية'),
                ('enter_english_translation', 'Enter English translation...', 'أدخل الترجمة الإنجليزية...'),
                ('enter_arabic_translation', 'Enter Arabic translation...', 'أدخل الترجمة العربية...'),
                ('enter_russian_translation', 'Enter Russian translation...', 'أدخل الترجمة الروسية...'),
                ('enter_chinese_translation', 'Enter Chinese translation...', 'أدخل الترجمة الصينية...'),
                ('enter_spanish_translation', 'Enter Spanish translation...', 'أدخل الترجمة الإسبانية...'),
                ('enter_tajik_translation', 'Enter Tajik translation...', 'أدخل الترجمة التاجيكية...'),
                ('enter_farsi_translation', 'Enter Farsi translation...', 'أدخل الترجمة الفارسية...'),
                ('enter_kazakh_translation', 'Enter Kazakh translation...', 'أدخل الترجمة الكازاخية...'),
                ('enter_azerbaijani_translation', 'Enter Azerbaijani translation...', 'أدخل الترجمة الأذربيجانية...'),
                ('all_rights_reserved', 'All rights reserved', 'جميع الحقوق محفوظة'),
                ('enter_username', 'Enter username', 'أدخل اسم المستخدم'),
                ('enter_password', 'Enter password', 'أدخل كلمة المرور'),
                ('secure_login_message', 'Please enter your credentials to access the system', 'يرجى إدخال بياناتك للوصول إلى النظام'),
                ('dashboard_description', 'Monitor and assess cybersecurity maturity across your organization', 'راقب وقيم نضج الأمن السيبراني في مؤسستك'),
                ('overview', 'Overview', 'نظرة عامة'),
                ('main_content_placeholder', 'Your cybersecurity assessment dashboard will appear here', 'ستظهر لوحة تقييم الأمن السيبراني هنا'),
                ('security_controls', 'Security Controls', 'ضوابط الأمان'),
                ('manage_security_controls', 'Manage and review security controls', 'إدارة ومراجعة ضوابط الأمان'),
                ('assessments', 'Assessments', 'التقييمات'),
                ('view_assessments', 'View assessment results and reports', 'عرض نتائج التقييم والتقارير'),
                ('quick_info', 'Quick Info', 'معلومات سريعة'),
                ('user', 'User', 'المستخدم'),
                ('role', 'Role', 'الدور'),
                ('language', 'Language', 'اللغة'),
                ('admin_tools', 'Admin Tools', 'أدوات الإدارة'),
                ('language_info', 'Language Settings', 'إعدادات اللغة'),
                ('language_change_info', 'You can change the interface language using the dropdown in the top navigation.', 'يمكنك تغيير لغة الواجهة باستخدام القائمة المنسدلة في التنقل العلوي.'),
            ]
            
            # Insert labels one by one with proper SQLAlchemy syntax
            with engine.connect() as conn:
                for key, en, ar in initial_labels:
                    try:
                        conn.execute(
                            text("INSERT INTO label (key, en, ar) VALUES (:key, :en, :ar)"),
                            {"key": key, "en": en, "ar": ar}
                        )
                    except Exception as e:
                        print(f"Warning: Could not insert label '{key}': {e}")
                        continue
                conn.commit()
            print(f"✓ Added {len(initial_labels)} initial labels")
            
        else:
            print("✓ Label table already exists")
        
        print("\n🎉 Database migration completed successfully!")
        print("\nNext steps:")
        print("1. Run your Flask application: python simple_app.py")
        print("2. Navigate to /admin/labels to manage translations")
        print("3. Use the language selector in the top navigation")
        
    except OperationalError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)