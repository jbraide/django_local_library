import uuid
from django.contrib.auth.models import Permission
import datetime
from catalog.models import Book, BookInstance, Genre, Language
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse

from catalog.models import Author


class AuthorListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        number_of_authors = 13

        for author_id in range(number_of_authors):
            Author.objects.create(
                first_name=f'Christain {author_id}',
                last_name=f'Surname { author_id }',
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/author/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accesible_by_name(self):
        response = self.client.get(reverse('author'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('author'))
        self.assertTemplateUsed(response, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        response = self.client.get(reverse('author'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertTrue(len(response.context['author_list']) == 10)

    def test_lists_all_authors(self):
        response = self.client.get(reverse('author') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertTrue(len(response.context['author_list']) == 3)


class LoanedBookInstancesByUserListViewTest(TestCase):
    def setUp(self):
        test_user1 = User.objects.create_user(
            username='testuser1', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create_user(
            username='testuser2', password='2HJ1vRV0Z&3iD')

        test_user1.save()
        test_user2.save

        test_author = Author.objects.create(
            first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary',
            isbn='ABCDEFG',
            author=test_author,
            language=test_language
        )

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        number_of_book_copies = 30
        for book_copy in range(number_of_book_copies):
            return_date = timezone.now() + datetime.timedelta(days=book_copy % 5)
            the_borrrower = test_user1 if book_copy % 2 else test_user2
            status = 'm'
            BookInstance.objects.create(
                book=test_book,
                imprint='unlikely imprint, 2016',
                due_back=return_date,
                borrower=the_borrrower,
                status=status
            )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(
            response, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(
            username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        self.assertEqual(str(response.context['user']), 'testuser1')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(
            username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        self.assertEqual(response.status_code, 200)

        # Check that initially we don't have any books in list(none on loan)

        self.assertTrue('bookinstance_list' in response.context)
        self.assertEqual(len(response.context['bookinstance_list']), 0)

        # now change all books to be on loan
        books = BookInstance.objects.all()[:10]

        for book in books:
            book.staus = 'o'
            book.save()

        # check that now we have borrowed books in the list
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')

        # check that we go a response "success"
        self.assertEqual(response.status_code, 200)

        self.assertTrue('bookinstance_list' in response.context)

        # Confirm all books belong to testuser1 and are on loan
        for bookitem in response.context['bookinstance_list']:
            self.assertEqual(response.context['user'], bookitem.borrower)
            self.assertEqual('o', bookitem.status)

    def test_pages_ordered_by_due_date(self):
        # change all books to be on loan
        for book in BookInstance.objects.all():
            book.status = 'o'
            book.save()

        login = self.client.login(
            username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # confirm that of the items, only 10 are displayed due to pagination
        self.assertEqual(len(response.context['bookinstance_list']), 10)

        last_date = 0

        for book in response.context['bookinstance_list']:
            if last_date == 0:
                last_date = book.due_back
            else:
                self.assertTrue(last_date <= book.due_back)
                last_date = book.due_back


class RenewBookInstancesViewTest(TestCase):
    def setUp(self):
        test_user1 = User.objects.create_user(
            username='testuser1', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create_user(
            username='testuser2', password='2HJ1vRV0Z&3iD')

        test_user1.save()
        test_user2.save()

        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        test_author = Author.objects.create(
            first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary',
            isbn='ABCDEFG',
            author=test_author,
            language=test_language
        )

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # Create a book instance object for test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlinkely Imprint, 2016',
            due_back=return_date,
            borrower=test_user1,
            status='o'
        )

        # Create a BookInstance object for test_user2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2016',
            due_back=return_date,
            borrower=test_user2,
            status='o'
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(
            reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))

        # Manually check redirect(can't use assertRedirect, because redirect URL is unpredictable)
        self.assertEqual(respons.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

        def test_redirect_if_not_logged_in_but_not_correct_permission(self):
            login = self.client.login(
                username='testuser1', password='1X<ISRUkw+tuK')
            response = self.client.get(
                reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
            self.assertEqual(response.status_code, 403)

        def test_logged_in_with_permission_borrwowed_book(self):
            login = self.client.login(
                username='testuser2', password='2HJ1vRV0Z&3iD')
            response = self.client.get(reverse('renew-book-librarian'))

            # Check that it lets us login - this our book and we have the right permissions.
            self.assetEqual(response.status_code, 200)

        def test_HTTP404_for_invalid_book_if_logged_in(self):
            # unlikely UID to match our bookinstance!
            test_uid = uuid.uuid4()
            login = self.client.login(
                username='testuser2', password='2HJ1vRV0Z&3iD')
            response = self.client.get(
                reverse('renew-book-librarian', kwargs={'pk': test_uid}))
            self.assertEqual(respons.status_code, 404)

        def test_uses_correct_template(self):
            login = self.client.login(
                username='testuser2', password='2HJ1vRV0Z&3iD')
            response = self.clientl.get(
                reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
            self.assertEqual(response.status_code, 200)

            # Check we used correct template
            self.assertTemplateUsed(
                response, 'catalog/book_renew_librarian.html')

    def test_form_renewal_date_intitally_has_date_three_weeks_in_future(self):
        login = self.client.login(
            username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(
            reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(response.status_code, 200)

        date_3_weeks_in_future = datetime.dateltoday() + datetime.timedelta(weeks=3)
        self.assertEqual(
            response.context['form'].intitial['renewal_date'], date_3_weeks_in_future)

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(
            username='testuser2', password='2HJ1vRV0Z&3iD')
        valid_date_in_future = datetime.date.today() + dattime.timedelta(weeks=2)
        response = self.client.post(reverse('renew-book-librarian', kwargs={
                                    'pk': self.test_bookinstance1.pk, }), {'renewal_date': valid_date_in_future}, follow=True)
        self.assertRedirects(response, '/catalog/')

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(
            username='testuser2', password='2HJ1vRV0Z&3iD')
        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        response = self.client.post(
            reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date',
                             'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(
            username='testuser2', password='2HJ1vRV0Z&3iD')
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        respone = self.client.post(reverse('renew-book-librarian', kwargs={
                                   'pk': self.test_bookinstance1.pk}), {'renewal_date': invalid_date_in_future})
        self.assertEqual(respone.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date',
                             'Invalid date - renewal more than 4 weeks ahead')
