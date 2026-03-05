from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from documents.email_utils import send_notification_email
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Тестирование отправки email уведомлений'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, help='Email получателя', required=False)

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("🔧 Проверка настроек EMAIL"))
        self.stdout.write("=" * 70)
        
        # Вывод текущих настроек
        self.stdout.write(f"\n📧 Настройки Email:")
        self.stdout.write(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        # Проверка пароля
        if hasattr(settings, 'EMAIL_HOST_PASSWORD') and settings.EMAIL_HOST_PASSWORD:
            self.stdout.write(f"   EMAIL_HOST_PASSWORD: ****** (установлен, {len(settings.EMAIL_HOST_PASSWORD)} символов)")
        else:
            self.stdout.write(self.style.ERROR("   EMAIL_HOST_PASSWORD: НЕ УСТАНОВЛЕН!"))
            return
        
        # Получить email для тестирования
        to_email = options.get('to')
        
        if not to_email:
            # Попробовать получить email первого пользователя
            try:
                user = User.objects.filter(email__isnull=False).exclude(email='').first()
                if user and user.email:
                    to_email = user.email
                    self.stdout.write(f"\n📬 Используется email пользователя {user.username}: {to_email}")
                else:
                    self.stdout.write(self.style.ERROR("\n❌ Не найден пользователь с email!"))
                    self.stdout.write("   Используйте: python manage.py test_email --to your@email.com")
                    return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n❌ Ошибка получения пользователя: {e}"))
                return
        
        self.stdout.write(f"\n📤 Отправка тестового письма на: {to_email}")
        self.stdout.write("-" * 70)
        
        # Тест 1: Простая отправка через send_mail
        self.stdout.write("\n1️⃣  Тест простой отправки (send_mail)...")
        try:
            result = send_mail(
                subject='Тест отправки email из ЭДО "Первый ключ"',
                message='Это тестовое письмо для проверки работы email-уведомлений.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            if result == 1:
                self.stdout.write(self.style.SUCCESS("   ✅ Письмо успешно отправлено!"))
            else:
                self.stdout.write(self.style.ERROR("   ❌ Письмо не отправлено (result=0)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка отправки: {e}"))
            self.stdout.write(f"\n💡 Возможные причины:")
            self.stdout.write(f"   1. Неверный пароль приложения Gmail")
            self.stdout.write(f"   2. Двухфакторная аутентификация не включена")
            self.stdout.write(f"   3. 'Ненадежные приложения' заблокированы в Gmail")
            self.stdout.write(f"   4. Проблемы с подключением к SMTP серверу")
            return
        
        # Тест 2: Отправка через send_notification_email
        self.stdout.write("\n2️⃣  Тест отправки через send_notification_email...")
        try:
            # Получаем пользователя для теста
            test_user = User.objects.filter(email=to_email).first()
            if not test_user:
                test_user = User.objects.filter(email__isnull=False).exclude(email='').first()
            
            if test_user:
                result = send_notification_email(
                    user=test_user,
                    subject='Тест HTML-уведомления из ЭДО',
                    message='Это тестовое HTML-письмо для проверки работы системы уведомлений. Если вы получили это письмо, значит настройки email работают корректно! ✅',
                    document=None
                )
                if result:
                    self.stdout.write(self.style.SUCCESS("   ✅ HTML-письмо успешно отправлено!"))
                else:
                    self.stdout.write(self.style.ERROR("   ❌ HTML-письмо не отправлено"))
            else:
                self.stdout.write(self.style.WARNING("   ⚠️  Пользователь не найден, пропущено"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка отправки HTML: {e}"))
        
        # Итоговая информация
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("✅ Тестирование завершено!"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"\n📬 Проверьте почтовый ящик: {to_email}")
        self.stdout.write("   (Также проверьте папку 'Спам')")
        self.stdout.write(f"\n⚙️  Настройка Gmail:")
        self.stdout.write("   1. Включите двухфакторную аутентификацию")
        self.stdout.write("   2. Создайте пароль приложения: https://myaccount.google.com/apppasswords")
        self.stdout.write("   3. Используйте пароль приложения в настройках EMAIL_HOST_PASSWORD")
        self.stdout.write("\n")
