import datetime
from catalog.models import Book, Author, BookInstance, Review, Profile
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required			# add authentication to pages like profile before access
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin   		# For Login requirements
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.admin.utils import construct_change_message
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q										# for using search queries 
from django.http import Http404										# redirect to 404	
from django.views import generic
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import SignUpForm, ReviewForm, BookForm, BookInstanceForm, CreateManagerForm

def error_404_view(request, exception):
    return render(request,'404.html')

# For Homepage / index
def index(request):
	"""View function for home page of site."""
	
	books = Book.objects.all().order_by('-id')[:3]					# get only the 3 newest books
	num_instances = BookInstance.objects.all().count()
    
    # Available books (status = 'a')
	num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    
    # The 'all()' is implied by default.    
	num_books = Book.objects.count()
	num_authors = Author.objects.count()
    
	# Number of visits to this view, as counted in the session variable.
	num_visits = request.session.get('num_visits', 0)				# initial count will be 0
	request.session['num_visits'] = num_visits + 1
	
	reviews = Review.objects.all().order_by('-id')[:3]				# get only the 3 latest book reviews
	authors = Author.objects.all().order_by('-id')[:5]				# get only the 5 latest authors
	
	context = {
		'num_books': num_books,
		'books': books,
		'num_instances': num_instances,
		'num_instances_available': num_instances_available,
		'num_authors': num_authors,
		'num_visits': num_visits,
		'reviews': reviews,
		'authors': authors,
    }

    # Render the HTML template index.html with the data in the context variable
	return render(request, 'index.html', context=context)
	
# ---------------------------------------------------------------------------------------------------------------------------------------- #
	
# For BookList page 
#(using class ListView, because it has most of the needed functionalities and follows Django best-practice) 	
class BookListView(generic.ListView):
	paginate_by = 12
	
	def get_queryset(self):
		queryset = Book.objects.all()
		if self.request.GET.get("q", None):
			selection = self.request.GET.get("browse")
			queryset = queryset.filter(Q(title__icontains=self.request.GET.get("q", None)))
		return queryset

# For BookDetails page	
class BookDetailView(generic.DetailView):
	model = Book
	
class BookInstanceView(generic.ListView):
	model = BookInstance
	template_name = 'manager/bookinstance_list.html'
	paginate_by = 10
	
	def get_queryset(self):
		if not self.request.user.is_staff and not self.request.user.groups.filter(name='Manager').exists():
			raise Http404
		else:
			queryset = BookInstance.objects.all()
			if self.request.GET.get("q", None):
				selection = self.request.GET.get("browse")
				queryset = queryset.filter(Q(book__title__icontains=self.request.GET.get("q", None)) |
										   Q(id__icontains=self.request.GET.get("q", None)))
			return queryset
	
# For AuthorList page	
class AuthorListView(generic.ListView):
	model = Author
	paginate_by = 10
	
# For AuthorDetails page
class AuthorDetailView(generic.DetailView):
	model = Author	

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
	"""Generic class-based view listing books on loan to current user."""
	model = BookInstance
	template_name = 'catalog/bookinstance_list_borrowed_user.html'
	paginate_by = 10

	def get_queryset(self):
		if not self.request.user.is_staff:
			return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='r').order_by('due_back')
		else:
			raise Http404

class ReviewsByUserListView(LoginRequiredMixin, generic.ListView):
	"""Generic class-based view listing books on loan to current user."""
	model = Review
	template_name = 'catalog/user_profile.html'
	paginate_by = 10

	def get_queryset(self):
		if not self.request.user.is_staff:
			return Review.objects.filter(user=self.request.user).order_by('date_published')
		else:
			raise Http404	

# ---------------------------------------------------------------------------------------------------------------------------------------- #
	
# For Signup page
def SignUpView(request):
	if not request.user.is_anonymous:
		return redirect('404')
	
	else:
		form = SignUpForm(request.POST)
		if form.is_valid():		
			user = form.save()
			user.refresh_from_db()	# used to handle synchronism issue
			user.profile.first_name = form.cleaned_data.get('first_name')
			user.profile.last_name = form.cleaned_data.get('last_name')
			user.profile.email = form.cleaned_data.get('email')
			user.profile.ID_num = form.cleaned_data.get('ID_num')		# set all user info as well as ID number and role to profile model 
			user.profile.role = form.cleaned_data.get('role')		
			LibraryMember = Group.objects.get(name='Library Members') 	# add a user to the Library Members group (default is teacher or student)
			LibraryMember.user_set.add(user)							# Library Members do not have any CRUD permissions 
			user.save()
			
			LogEntry.objects.log_action(
					user_id=user.id,
					content_type_id=ContentType.objects.get_for_model(user).pk,
					object_id=user.id,
					object_repr=str(user.__str__()),
					action_flag=ADDITION,
					change_message= construct_change_message(form, None, True)			# Set to False when edited, set to True when added
					)
			
			messages.success(request, "Account saved! Please login again to verify it is you!")

			return redirect('login')	# redirect to homepage once account has been successfully registered 
		else:
			form = SignUpForm()
	return render(request, '../templates/registration/signup.html', {'form': form})


# For Borrowing Books		
def BorrowBookView(request, pk):
	book_instance = get_object_or_404(BookInstance, pk=pk)
	if request.user.is_staff:
		return redirect('404')
	
	if request.method == 'POST':
		if request.user.is_authenticated:
		
			book_instance.borrower = request.user
			book_instance.due_back = datetime.date.today() + datetime.timedelta(weeks=3)	# set book borrow time to 3 weeks 
			book_instance.status = 'r'
			book_instance.save()
			
			LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(book_instance).pk,
				object_id=book_instance.id,
				object_repr=str(book_instance.__str__()),
				action_flag=CHANGE,
				change_message= '[{"changed": {"fields": ["Status", "Due back", "Borrower"]}}]'			# Set to False when edited, set to True when added
				)
			
			messages.success(request, 'You have now borrowed this book!')
			return HttpResponseRedirect(reverse('my-borrowed'))
		else:
			return redirect('login')

	context = {
		'book_instance': book_instance,
	}

	return render(request, 'catalog/book_detail.html', context)	# is ignored
	

# For Leaving Book Review
@login_required
def ReviewBookView(request, pk):
	book = get_object_or_404(Book, pk=pk)
	
	if request.user.is_staff:
		return redirect('404')

	if request.method == 'POST':
		form = ReviewForm(request.POST)
		if form.is_valid():
			review = form.save()
			review.book = book
			review.user = request.user
			review.save()
			
			LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(review).pk,
				object_id=review.id,
				object_repr=str(review.__str__()),
				action_flag=ADDITION,
				change_message= construct_change_message(form, None, True)			# Set to False when edited, set to True when added
				)
			
			messages.success(request, 'Your review has been posted to the website!')
			return redirect('book-detail', pk=pk)		# return to the current book-detail page 
		else:
			messages.error(request, 'Please correct the error below.')
	else:
		form = ReviewForm()
	
	return render(request, 'catalog/book_review.html', {
		'form': form,
		'book': book,
	})

# For Password Change Form		
@login_required
def ChangePasswordView(request):
	if request.user.is_staff:
		return redirect('404')

	if request.method == 'POST':
		form = PasswordChangeForm(request.user, request.POST)
		if form.is_valid():
			user = form.save()
			update_session_auth_hash(request, user)  # Important!
			
			LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(user).pk,
				object_id=user.id,
				object_repr=str(user.__str__()),
				action_flag=CHANGE,
				change_message= construct_change_message(form, None, False)			# Set to False when edited, set to True when added
				)
			
			messages.success(request, 'Your password was successfully updated!')
			return redirect('user-profile', username=user.username)
		else:
			messages.error(request, 'Please correct the error below.')
	else:
		form = PasswordChangeForm(request.user)
	return render(request, 'catalog/change_password.html', {
		'form': form
	})
	
# ---------------------------------------------------------------------------------------------------------------------------------------- #

# Manager Side

# For Delete Book
def DeleteBookView(request, book_id=None):
	if request.user.is_staff and request.user.groups.filter(name='Manager').exists():
		book_to_delete = Book.objects.get(id=book_id)
		
		LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(book_to_delete).pk,
				object_id=book_to_delete.id,
				object_repr=str(book_to_delete.__str__()),
				action_flag=DELETION,
				)
		
		book_to_delete.delete()
		messages.success(request, 'The book copy has been deleted!')
		return HttpResponseRedirect(reverse('books'))
	else:
		return redirect('404')
		
# For Add Book		
def AddBookView(request):
	if not request.user.is_staff or not request.user.groups.filter(name='Manager').exists():
		return redirect('404')

	if request.method == "POST":
		form = BookForm(request.POST, request.FILES)
		if form.is_valid():
			book = form.save(commit=False)
			book.save()
			form.save_m2m()
			
			LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(book).pk,
				object_id=book.id,
				object_repr=str(book.__str__()),
				action_flag=ADDITION,
				change_message= construct_change_message(form, None, True)			# Set to False when edited, set to True when added
				)
			
			messages.success(request, 'You have now added this book to the library!')
			return HttpResponseRedirect(reverse('books'))
	else:
		form = BookForm()
	return render(request, "manager/add_book.html", {"form": form})
	
# For Edit Book
def EditBookView(request, pk):
	if not request.user.is_staff or not request.user.groups.filter(name='Manager').exists():
		return redirect('404')

	book = Book.objects.get(pk=pk)
	if request.method == 'POST':
		form = BookForm(request.POST, files=request.FILES, instance=book)
		if form.is_valid():
			book = form.save()
			
			LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(book).pk,
				object_id=book.id,
				object_repr=str(book.__str__()),
				action_flag=CHANGE,
				change_message= construct_change_message(form, None, False)			# Set to False when edited, set to True when added
				)
			
			messages.success(request, 'Your edits to this book has been saved!')
			return HttpResponseRedirect(reverse('books'))
		else:
			form = BookForm(instance=book)
	else:
		form = BookForm(instance=book)
	return render(request, "manager/edit_book.html", {'form':form, 'book':book})
	
# For Delete Book Instance / Copy
def DeleteBookInstanceView(request, copy_id=None):
	if request.user.is_staff and request.user.groups.filter(name='Manager').exists():
		copy_to_delete = BookInstance.objects.get(id=copy_id)
		
		LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(copy_to_delete).pk,
				object_id=copy_to_delete.id,
				object_repr=str(copy_to_delete.__str__()),
				action_flag=DELETION,
				)
		
		copy_to_delete.delete()
		messages.success(request, 'The book copy has been deleted!')
		return HttpResponseRedirect(reverse('book-copies'))
	else:
		return redirect('404')
		
# For Add Book Instance / Copy		
def AddBookInstanceView(request):
	if not request.user.is_staff or not request.user.groups.filter(name='Manager').exists():
		return redirect('404')

	if request.method == "POST":
		form = BookInstanceForm(request.POST)
		if form.is_valid():
			bookinstance = form.save()
			bookinstance.save()
			
			LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(bookinstance).pk,
				object_id=bookinstance.id,
				object_repr=str(bookinstance.__str__()),
				action_flag=ADDITION,
				change_message= construct_change_message(form, None, True)			# Set to False when edited, set to True when added
				)
			
			messages.success(request, 'You have now added a copy for this book!')
			return HttpResponseRedirect(reverse('book-copies'))
	else:
		form = BookInstanceForm()
	return render(request, "manager/add_book_instance.html", {"form": form})
	
# For Edit Book Instance / Copy	
def EditBookInstanceView(request, pk):
	if not request.user.is_staff or not request.user.groups.filter(name='Manager').exists():
		return redirect('404')

	copy = BookInstance.objects.get(pk=pk)
	if request.method == 'POST':
		form = BookInstanceForm(request.POST, instance=copy)
		if form.is_valid():
			bookinstance = form.save()
					
			LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(bookinstance).pk,
				object_id=bookinstance.id,
				object_repr=str(bookinstance.__str__()),
				action_flag=CHANGE,
				change_message= construct_change_message(form, None, False)			# Set to False when edited, set to True when added
				)
			
			messages.success(request, 'Your edits to this book copy has been saved!')
			return HttpResponseRedirect(reverse('book-copies'))
		else:
			form = BookInstanceForm(instance=copy)
	else:
		form = BookInstanceForm(instance=copy)
	return render(request, "manager/edit_book_instance.html", {'form':form, 'copy':copy})

# ---------------------------------------------------------------------------------------------------------------------------------------- #

# Administrator Side

# For Admin Logs
def SystemLogsView(request):
	if not request.user.is_staff or not request.user.groups.filter(name='Administrator').exists():
		return redirect('404')
		
	logs = LogEntry.objects.all().order_by("-id")
	return render(request, "administrator/system_logs.html", {'logs': logs},)
	
# For Managers page
class ManagerListView(generic.ListView):
	queryset = User.objects.filter(groups__name__in=['Manager'])
	template_name = 'administrator/manager_list.html'
	paginate_by = 10
	
	def get_queryset(self):
		if not self.request.user.is_staff or not self.request.user.groups.filter(name='Administrator').exists():
			raise Http404
		else:
			queryset = User.objects.filter(groups__name__in=['Manager'])
			if self.request.GET.get("q", None):
				selection = self.request.GET.get("browse")
				queryset = queryset.filter(Q(username__icontains=self.request.GET.get("q", None)) |
										   Q(first_name__icontains=self.request.GET.get("q", None)) |
										   Q(last_name__icontains=self.request.GET.get("q", None))
										   )
			return queryset
			
# For Add Manager page (Same with signup but with different permissions)
def AddManagerView(request):
	if not request.user.is_staff or not request.user.groups.filter(name='Administrator').exists():
		return redirect('404')
	
	form = CreateManagerForm(request.POST)
	if form.is_valid():		
		user = form.save()
		user.refresh_from_db()	# used to handle synchronism issue
		user.profile.first_name = form.cleaned_data.get('first_name')
		user.profile.last_name = form.cleaned_data.get('last_name')
		user.profile.email = form.cleaned_data.get('email')
		user.profile.ID_num = form.cleaned_data.get('ID_num')		# set all user info as well as ID number and role to profile model 
		user.profile.role = 'manager'		
		LibraryMember = Group.objects.get(name='Manager') 	# add a user to the Manager group 
		LibraryMember.user_set.add(user)							# Managers have permissions for books and bookinstances  
		user.is_staff = True
		
		user.save()
		
		LogEntry.objects.log_action(
				user_id=request.user.id,
				content_type_id=ContentType.objects.get_for_model(user).pk,
				object_id=user.id,
				object_repr=str(user.__str__()),
				action_flag=ADDITION,
				change_message= construct_change_message(form, None, True)			# Set to False when edited, set to True when added
				)
		
		messages.success(request, 'The new manager is now added to the system!')
		
		return redirect('../managers')	# redirect to manager list page once account has been successfully registered 
	else:
		form = CreateManagerForm()
	return render(request, 'administrator/add_manager.html', {'form': form})
