from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation


class RegisterForm(forms.Form):
    username = forms.CharField(  # تغییر از email به username
        label='نام کاربری',
        max_length=100,
        widget=forms.TextInput(),
        validators=[
            validators.MaxLengthValidator(100),
        ]
    )
    email = forms.EmailField(
        label='ایمیل',
        widget=forms.EmailInput(),
        help_text='برای بازیابی رمز عبور در صورت فراموشی، به این ایمیل نیاز است.',
    )
    password = forms.CharField(
        label='کلمه عبور',
        widget=forms.PasswordInput(),
        validators=[validators.MaxLengthValidator(100)],
    )
    confirm_password = forms.CharField(
        label='تکرار کلمه عبور',
        widget=forms.PasswordInput(),
        validators=[validators.MaxLengthValidator(100)],
    )

    def clean_username(self):
        # حذف فاصله‌های اضافی ابتدا/انتها تا نام‌کاربری‌های ظاهراً متفاوت ولی یکسان ثبت نشن
        username = self.cleaned_data.get('username', '')
        return username.strip()

    def clean_email(self):
        from .models import User
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('این ایمیل قبلاً ثبت شده است')
        return email

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if not password or not confirm_password:
            raise ValidationError('هر دو فیلد کلمه عبور الزامی است')
        if password != confirm_password:
            raise ValidationError('کلمه عبور و تکرار کلمه عبور مغایرت دارند')
        return confirm_password

    def clean(self):
        # اعمال AUTH_PASSWORD_VALIDATORS تعریف‌شده در settings.py
        # (پیش از این تعریف شده بودن ولی هیچ‌جا صدا زده نمی‌شدن)
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            from .models import User
            temp_user = User(username=username , email='')
            try:
                password_validation.validate_password(password, user=temp_user)
            except ValidationError as error:
                self.add_error('password', error)
        return cleaned_data
    
class LoginForm(forms.Form):
    username = forms.CharField(  # تغییر از email به username
        label='نام کاربری',
        max_length=100,
        widget=forms.TextInput(),
        validators=[
            validators.MaxLengthValidator(100),
        ]
    )
    password = forms.CharField(
        label='کلمه عبور',
        widget=forms.PasswordInput(),
        validators=[validators.MaxLengthValidator(100)],
    )
