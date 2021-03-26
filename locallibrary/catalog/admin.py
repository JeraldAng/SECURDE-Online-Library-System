from django.contrib import admin
from .models import Author, Book, BookInstance, Review

# Register your models here.

# Register the admin class with the associated model
class BooksInline(admin.TabularInline):
	model = Book.author.through
	extra = 0

class BooksInstanceInline(admin.TabularInline):
	model = BookInstance
	extra = 0

# Define the admin class
class BookAdmin(admin.ModelAdmin):
	list_display = ('title', 'display_authors')
	inlines = [BooksInstanceInline]	

class AuthorAdmin(admin.ModelAdmin):
	list_display = ('last_name', 'first_name', 'date_of_birth', 'date_of_death')
	fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]
	inlines = [BooksInline]

class BookInstanceAdmin(admin.ModelAdmin):
	list_display = ('book', 'status', 'borrower', 'due_back', 'id')
	list_filter = ('status', 'due_back')
	
	fieldsets = (
		(None, {
			'fields': ('book', 'id')
		}),
		('Availability', {
			'fields': ('status', 'due_back', 'borrower')
		}),
	)
	
	# only show Users that are NOT staff in borrower field 
	def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
		if db_field.name == "borrower":
			kwargs["queryset"] = User.objects.filter(is_staff=False)
		return super(BookInstanceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
	
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('book', 'rating', 'date_published', 'user', 'id')	

admin.site.register(Book, BookAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(BookInstance, BookInstanceAdmin)
admin.site.register(Review, ReviewAdmin)

# Add Profile Details to User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from .models import Profile

# Define an inline admin descriptor for User model
# which acts a bit like a singleton
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile details'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
	inlines = (ProfileInline,BooksInstanceInline)
	
	fieldsets = (
		(None, {'fields': ('username', 'password')}),
		(('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
		(('Permissions'), {'fields': ('is_active', 'is_staff', 'groups',)}),
		(('Important dates'), {'fields': ('last_login', 'date_joined')}),
	)
	
	admin_fieldsets = (
		(None, {'fields': ('username', 'password')}),
		(('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
		(('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		(('Important dates'), {'fields': ('last_login', 'date_joined')}),
	)

	# get only the manager accounts if user is administrator
	def get_queryset(self, request):
		qs = super(UserAdmin, self).get_queryset(request)
		if request.user.groups.filter(name='Administrator').exists():
			qs = qs.filter(profile__role='manager')
		return qs
	
	# remove permissions and super user fields if user is administrator 
	def get_fieldsets(self, request, obj=None):
		if request.user.is_superuser:
			return self.admin_fieldsets
		else:
			return super(UserAdmin, self).get_fieldsets(request, obj=obj)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Admin Logs
from django.contrib.admin.models import LogEntry

admin.site.register(LogEntry)




