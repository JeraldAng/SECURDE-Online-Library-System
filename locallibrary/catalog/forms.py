from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .import models

USER_ROLE = [('teacher','Teacher'),('student','Student')]
STAR_RATING = [('0','0 Stars'),('1','1 Star'),('2','2 Stars'),('3','3 Stars'),('4','4 Stars'),('5','5 Stars')]
COPY_STATUS = [('a','Available'),('r','Reserved')]

class SignUpForm(UserCreationForm):
	role = forms.ChoiceField(choices=USER_ROLE, widget=forms.RadioSelect,)
	first_name = forms.CharField(max_length=30,
	widget=forms.TextInput(attrs={'autofocus': 'autofocus'}))	# This makes the cursor focus on first name input; it defaults to username
	last_name = forms.CharField(max_length=30)
	username = forms.CharField(max_length=30)
	ID_num = forms.IntegerField(help_text='This must be a 10 digit number')
	email = forms.EmailField(max_length=200)

	class Meta:
		model = User
		fields = ('first_name', 'last_name', 'username', 'email', 'ID_num', 'role', 'password1', 'password2')
	
class ReviewForm(forms.ModelForm):
	rating = forms.ChoiceField(choices=STAR_RATING, widget=forms.RadioSelect,)
	review = forms.CharField(widget=forms.Textarea)
	
	class Meta:
		model = models.Review 
		fields = ('rating', 'review')
		
class BookForm(forms.ModelForm):
	title = forms.CharField(max_length=200)
	author = forms.ModelMultipleChoiceField(queryset=models.Author.objects.all(), widget=forms.SelectMultiple(attrs={'multiple': '', 'class': "form-control"}), help_text="Tip: Hold Ctrl then click for selecting multiple authors.")
	publisher = forms.CharField(max_length=200)
	year = forms.CharField(widget=forms.TextInput(attrs={'min':'1400','max': '9999','type': 'number'}))
	isbn = forms.CharField(max_length=13)
	call_number = forms.CharField(widget=forms.TextInput(attrs={'min':'000','max': '999','type': 'number'}))
	summary = forms.CharField(max_length=1500, widget=forms.Textarea(attrs={'rows':4, 'cols':75}))
	book_cover = forms.ImageField(required=False)
	
	class Meta:
		model = models.Book 
		fields = ('title', 'author', 'publisher', 'year', 'isbn', 'call_number', 'summary', 'book_cover')
		
class BookInstanceForm(forms.ModelForm):
	id = forms.UUIDField(required=False, help_text="Tip: Leave empty to have the system autogenerate a new one!")
	book = forms.ModelChoiceField(queryset=models.Book.objects.all(), widget=forms.Select(attrs={'class': "form-control"}),)
	due_back = forms.DateField(required=False)
	borrower = forms.ModelChoiceField(queryset=models.User.objects.filter(is_staff=False), widget=forms.Select(attrs={'class': "form-control"}),required=False)
	status = forms.ChoiceField(choices=COPY_STATUS, widget=forms.RadioSelect, help_text="If Reserved, kindly fill in as well the two inputs below.")
	
	class Meta:
		model = models.BookInstance 
		fields = ('id', 'book', 'status', 'due_back', 'borrower')

class CreateManagerForm(UserCreationForm):
	first_name = forms.CharField(max_length=30,
	widget=forms.TextInput(attrs={'autofocus': 'autofocus'}))	# This makes the cursor focus on first name input; it defaults to username
	last_name = forms.CharField(max_length=30)
	username = forms.CharField(max_length=30)
	ID_num = forms.IntegerField(help_text='This must be a 10 digit number')
	email = forms.EmailField(max_length=200)

	class Meta:
		model = User
		fields = ('first_name', 'last_name', 'username', 'email', 'ID_num', 'password1', 'password2')
	

	


