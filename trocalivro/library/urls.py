from django.urls import path, include
from library import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_book, name='search-books'),
    path('book/', views.book_add, name='book-add'), 
    path('book/<int:id>', views.book_detail_view, name='book-detail'),
    path('profile/', views.profile, name='users-profile'),
    path('profile/edit', views.edit_profile, name='users-edit'),
    path('profile/sends', views.send_books, name='send-books'),
    path('profile/received', views.received_books, name='received-books'),
    
    path('signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),

    # Path da solicitação de troca de um livro 
    path('book/<int:id>/request/', views.request, name='book-request')
]