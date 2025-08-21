from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from . models import Account

# Register your models here.

class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'last_login', 'date_joined','seller_status','is_active')
    list_display_links = ('email', )
    readonly_fields = ('last_login', 'date_joined')
    list_editable = ("seller_status",)
    ordering = ('-date_joined',) #- date shows in descending order
    
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    
    
admin.site.register(Account, AccountAdmin)
