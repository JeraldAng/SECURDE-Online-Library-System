from django.contrib import admin
from django.urls import path
from . import views 
from django.views.generic import TemplateView

import django

def custom_page_not_found(request):
	return django.views.defaults.page_not_found(request, None)

urlpatterns = [
	path('', views.index, name='index'),	# homepage
	path('books/', views.BookListView.as_view(), name='books'), # booklist page: view is implemented as a class, thus, as_view() class method is used
	path('book/<int:pk>', views.BookDetailView.as_view(), name='book-detail'), # book details page: <int:pk> captures the book id and places it in primary key pk
	path('authors/', views.AuthorListView.as_view(), name='authors'), # authorlist page
	path('author/<int:pk>', views.AuthorDetailView.as_view(), name='author-detail'), # author details page 
    path('mybooks/', views.LoanedBooksByUserListView.as_view(), name='my-borrowed'), # for on loan books
	path('signup/', views.SignUpView, name='signup'), # for signup page
	path('profile/<username>', views.ReviewsByUserListView.as_view(), name='user-profile'),	 # for user profile page 
	path('book/<uuid:pk>/borrow', views.BorrowBookView, name='borrow-book'), # borrow book path 
	path('book/<int:pk>/review', views.ReviewBookView, name='review-book'), # review book path
	path('password/', views.ChangePasswordView, name='change-password'), # change password path 
	path('404/', custom_page_not_found, name='404'),	# 404 path
	path('books/<book_id>/delete', views.DeleteBookView, name='delete-book'),	# delete book path
	path('books/add', views.AddBookView, name='add-book'),	# add book path
	path('books/<int:pk>/edit', views.EditBookView, name='edit-book'),	# edit book path
	path('copies', views.BookInstanceView.as_view(), name='book-copies'),	# book instances page 
	path('copies/<copy_id>/delete', views.DeleteBookInstanceView, name='delete-copy'),	# delete book instances path 
	path('copies/add', views.AddBookInstanceView, name='add-copy'),	# add book instances path 
	path('copies/<uuid:pk>/edit', views.EditBookInstanceView, name='edit-copy'),	# edit book instances path 
	path('logs/', views.SystemLogsView, name='system-logs'),	# for system logs page 
	path('managers/', views.ManagerListView.as_view(), name='managers'),	# for managers page 
	path('managers/add', views.AddManagerView, name='add-manager'),	# for add manager path 
	path('timeout/', TemplateView.as_view(template_name="session_timeout.html"), name='timeout'),	# session timeout 
]