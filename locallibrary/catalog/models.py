from django.db import models
from django.urls import reverse # Used to generate URLs by reversing the URL patterns
import uuid # Required for unique book instances
import datetime # for publishing year
from django.core.validators import MaxValueValidator, MinValueValidator # Used for setting a max and min value for integers  
from datetime import date

from django.contrib.auth.models import User  # Required to assign User as a borrower

# Create your models here.
		
class Book(models.Model):
	"""Model representing a book (but not specify copy of a book)."""
	title = models.CharField(max_length=200, help_text='Enter the title of the book')
	
	# ManytoManyField used because author can have many books. Books can be written by many authors.
	# Author as a string rather than object because it hasn't been declared yet in the file
	#author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True, help_text='Enter the author/s of the book')
	author = models.ManyToManyField('Author', help_text='Enter the author/s of the book')
	
	publisher = models.CharField(max_length=200, help_text='Enter the publisher of the book')
	year = models.PositiveSmallIntegerField(
		default=datetime.datetime.now().year, 
		help_text='Enter the publication year',
		validators=[
            MaxValueValidator(9999),		# max year is 9999
            MinValueValidator(1400)			# min year is 1400 (oldest mechanically published book is around 1450s)
        ]
	)
	isbn = models.CharField('ISBN', max_length=13, help_text='13 Character ISBN number')
	call_number = models.PositiveSmallIntegerField(
		default='000',
		help_text='Call Number of the book',
		validators=[
            MaxValueValidator(999),			# max call number is 999, from Dewey Decimal System 
            MinValueValidator(000)			# min call number is 000, from Dewey Decimal System 
        ]
	)
	
	summary = models.TextField(max_length=1000, help_text='Enter a brief description of the book')
	book_cover = models.ImageField(default='bookcovers/no-cover.jpg', upload_to='bookcovers', height_field=None, width_field=None, max_length=100)

	
	class Meta:
		ordering = ['title']
	
	def __str__(self):
		"""String for representing the Model object."""
		return self.title
		
	def display_authors(self):
		"""Create a string for the Authors. This is required to display authors in Admin."""
		#return ', '.join(author.last_name + ", " + author.first_name for author in self.author.all()[:3])			# display only the top 3 authors
		return ', '.join(author.last_name + ", " + author.first_name for author in self.author.all())

	display_authors.short_description = 'Author/s'	
				
	def get_absolute_url(self):
		"""Returns the url to access a detail record for this book."""
		return reverse('book-detail', args=[str(self.id)])
		
class BookInstance(models.Model):
	"""Model representing a specific copy of a book (i.e. that can be borrowed from the library)."""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID')
	book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True)
	due_back = models.DateField(null=True, blank=True)
	borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

	@property
	def is_overdue(self):
		if self.due_back and date.today() > self.due_back:
			return True
		return False

	LOAN_STATUS = (
		('a', 'Available'),
		('r', 'Reserved'),
	)
	
	status = models.CharField(
		max_length=1,
		choices=LOAN_STATUS,
		blank=True,
		default='a',
		help_text='Book availability',
	)
	
	class Meta:
		ordering = ['due_back']
		permissions = (("can_mark_returned", "Set book as returned"),)
	
	def __str__(self):
		"""String for representing the Model object."""
		return f'{self.id} ({self.book.title})'
		
class Author(models.Model):
	"""Model representing an author."""
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	date_of_birth = models.DateField(null=True, blank=True)
	date_of_death = models.DateField('Died', null=True, blank=True)
	
	class Meta:
		ordering = ['last_name', 'first_name']
		
	def __str__(self):
		"""String for representing the Model object."""
		return f'{self.last_name}, {self.first_name}'
		
	def get_absolute_url(self):
		"""Returns the url to access a particular author instance."""
		return reverse('author-detail', args=[str(self.id)])
		
class Review(models.Model):
	"""Model representing a review for a certain book."""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID')
	book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True)
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	date_published = models.DateField(default=datetime.datetime.today, editable=False)		# hide the date_published since it should not be edited, set to today always 
	rating = models.PositiveSmallIntegerField(
		help_text='Enter book rating out of 5',
		validators=[
            MaxValueValidator(5),		# max rating is 5/5
            MinValueValidator(0)		# min rating is 0/5
        ]
	)
	review = models.TextField(max_length=1000, help_text='Enter book review')
	
	class Meta:
		ordering = ['date_published']

	def __str__(self):
		"""String for representing the Model object."""
		return f'{self.id} ({self.book.title})'
		

# Extending the existing User model (add more details such as ID)		
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
	user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name='profile')
	ID_num = models.CharField(max_length=10)
	role = models.CharField(max_length=20, blank=True)
	
	def __str__(self):
		return self.user.username

@receiver(post_save, sender=User)
def update_profile_signal(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)
	instance.profile.save()
	

	
