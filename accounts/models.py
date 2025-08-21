from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class MyAccountManager(BaseUserManager):
    
    # Creating normal user
    def create_user(self, first_name, last_name, username, email, password=None):
        if not email:
            raise ValueError('User must have an email address')
        
        if not username:
            raise ValueError('User must have a username')
        
        user = self.model(
            email = self.normalize_email(email), 
            username = username,
            first_name = first_name,
            last_name = last_name
        )
        
        user.set_password(password)
        user.is_active = False
        user.save(using=self._db)
        return user
    
    # Creating superuser
    def create_superuser(self, first_name, last_name, email, username, password):
        
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name= first_name,
            last_name=last_name
        )
        
        # Setting permission
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user
        
        

class Account(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    SELLER_STATUS = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('banned', 'Banned'),
        ('none', 'None'),
    ]
    
    first_name = models.CharField(max_length=500)
    last_name = models.CharField(max_length=500)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=50)
    profile_picture = models.ImageField(
        upload_to='photos/users/',
        blank=True, 
        null=True
    )
    payment_qr = models.ImageField(upload_to="photos/user_qr/", blank=True, null=True)
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )
    
    seller_status = models.CharField(
        max_length=20,
        choices=SELLER_STATUS,
        default='none'
    )
    
    # Required
    date_joined = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)
    
    # To login using email address
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username', 'first_name', 'last_name'
        
    ]
    
    # Notifying we are using this for these operations
    objects = MyAccountManager()
    
    def __str__(self):
        return self.email
    
    # If user is admin they have all permission
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, add_label):
        return True
    
    def get_full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email
    
    def is_seller_active(self) -> bool:
        return self.seller_status == 'active'
    
