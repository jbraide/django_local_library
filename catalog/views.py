import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .models import Book, BookInstance, Author, Genre

from catalog.forms import RenewBookForm


def index(request):
    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Available books (status='a')
    num_instances_available = BookInstance.objects.filter(
        status__exact='a').count()
    num_authors = Author.objects.count()

    # Number of visits to this view, as counted in the session variable
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits
    }

    return render(request, 'index.html', context)


# Renew Book Librarian form F&N
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If it is a POST request thenprocess the Form data
    if request.method == "POST":
        form = RenewBookForm(request.POST)

        # Check if the form is valid

        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # Redirect to anew URL
            # return HttpResponseRedirect(reverse('all-borrowed'))
            return redirect('/catalog/')
        else:
            proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
            form = RenewBookForm(
                initial={'renewal_date': proposed_renewal_date})

        context = {
            'form': form,
            'book_instance': book_instance
        }

        return render(request, 'catalog/book_renew_librarian.html', context)


# Book list


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

# Book detail


class BookDetailView(generic.DetailView):
    model = Book

# Author list


class AuthorListView(generic.ListView):
    model = Author

# Author Details


class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'


class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('author')


class BookCreate(CreateView):
    model = Book
    # fields = ['title', 'author', 'summary', 'isbn', '']
    fields = '__all__'
