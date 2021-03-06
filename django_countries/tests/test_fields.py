from __future__ import unicode_literals
import django
from django.db import IntegrityError
from django.forms import Select
from django.forms.models import modelform_factory
from django.test import TestCase
from django.utils.encoding import force_text
try:
    from unittest import skipIf
except:
    from django.utils.unittest import skipIf

from django_countries import fields
from django_countries.tests.models import Person, AllowNull


class TestCountryField(TestCase):

    def test_logic(self):
        person = Person(name='Chris Beaven', country='NZ')

        self.assertEqual(person.country, 'NZ')
        self.assertNotEqual(person.country, 'ZZ')

        self.assertTrue(person.country)
        person.country = ''
        self.assertFalse(person.country)

    def test_only_from_instance(self):
        self.assertRaises(AttributeError, lambda: Person.country)

    @skipIf(
        django.VERSION < (1, 7), "Field.deconstruct introduced in Django 1.7")
    def test_deconstruct(self):
        field = Person._meta.get_field('country')
        self.assertEqual(
            field.deconstruct(),
            ('country', 'django_countries.fields.CountryField', [],
             {'max_length': 2}))

    def test_text(self):
        person = Person(name='Chris Beaven', country='NZ')
        self.assertEqual(force_text(person.country), 'NZ')

    def test_name(self):
        person = Person(name='Chris Beaven', country='NZ')
        self.assertEqual(person.country.name, 'New Zealand')

    def test_flag(self):
        person = Person(name='Chris Beaven', country='NZ')
        with self.settings(STATIC_URL='/static-assets/'):
            self.assertEqual(
                person.country.flag, '/static-assets/flags/nz.gif')

    def test_custom_field_flag_url(self):
        person = Person(name='Chris Beaven', country='NZ', other_country='US')
        self.assertEqual(
            person.other_country.flag, '//flags.example.com/us.gif')

    def test_COUNTRIES_FLAG_URL_setting(self):
        # Custom relative url
        person = Person(name='Chris Beaven', country='NZ')
        with self.settings(COUNTRIES_FLAG_URL='img/flag-{code_upper}.png',
                           STATIC_URL='/static-assets/'):
            self.assertEqual(
                person.country.flag, '/static-assets/img/flag-NZ.png')
        # Custom absolute url
        with self.settings(COUNTRIES_FLAG_URL='https://flags.example.com/'
                           '{code_upper}.PNG'):
            self.assertEqual(
                person.country.flag, 'https://flags.example.com/NZ.PNG')

    def test_blank(self):
        person = Person.objects.create(name='The Outsider')
        self.assertEqual(person.country, '')

        person = Person.objects.get(pk=person.pk)
        self.assertEqual(person.country, '')

    def test_len(self):
        person = Person(name='Chris Beaven', country='NZ')
        self.assertEqual(len(person.country), 2)

        person = Person(name='The Outsider')
        self.assertEqual(len(person.country), 0)

    def test_lookup_text(self):
        Person.objects.create(name='Chris Beaven', country='NZ')
        Person.objects.create(name='Pavlova', country='NZ')
        Person.objects.create(name='Killer everything', country='AU')

        lookup = Person.objects.filter(country='NZ')
        names = lookup.order_by('name').values_list('name', flat=True)
        self.assertEqual(list(names), ['Chris Beaven', 'Pavlova'])

    def test_lookup_country(self):
        Person.objects.create(name='Chris Beaven', country='NZ')
        Person.objects.create(name='Pavlova', country='NZ')
        Person.objects.create(name='Killer everything', country='AU')

        oz = fields.Country(code='AU', flag_url='')
        lookup = Person.objects.filter(country=oz)
        names = lookup.values_list('name', flat=True)
        self.assertEqual(list(names), ['Killer everything'])

    def test_save_empty_country(self):
        Person.objects.create(name='The Outsider')
        person = Person.objects.get()
        self.assertEqual(person.country, '')

    def test_save_null_country_allowed(self):
        AllowNull.objects.create(country=None)
        nulled = AllowNull.objects.get()
        self.assertIsNone(nulled.country)

    def test_save_null_country_not_allowed(self):
        self.assertRaises(
            IntegrityError,
            Person.objects.create, name='The Outsider', country=None)

    def test_create_modelform(self):
        Form = modelform_factory(Person, fields=['country'])
        form_field = Form().fields['country']
        self.assertTrue(isinstance(form_field.widget, Select))

    def test_render_form(self):
        Form = modelform_factory(Person, fields=['country'])
        Form().as_p()


class TestCountryObject(TestCase):

    def test_hash(self):
        country = fields.Country(code='XX', flag_url='')
        self.assertEqual(hash(country), hash('XX'))

    def test_repr(self):
        country1 = fields.Country(code='XX')
        country2 = fields.Country(code='XX', flag_url='')
        self.assertEqual(
            repr(country1),
            'Country(code={0})'.format(repr('XX')))
        self.assertEqual(
            repr(country2),
            'Country(code={0}, flag_url={1})'.format(repr('XX'), repr('')))

    def test_no_blank_code(self):
        self.assertRaises(ValueError, fields.Country, code='', flag_url='')

    def test_ioc_code(self):
        country = fields.Country(code='NL', flag_url='')
        self.assertEqual(country.ioc_code, 'NED')

    def test_country_from_ioc_code(self):
        country = fields.Country.country_from_ioc('NED')
        self.assertEqual(country, fields.Country('NL', flag_url=''))

    def test_country_from_blank_ioc_code(self):
        country = fields.Country.country_from_ioc('')
        self.assertIsNone(country)

    def test_country_from_nonexistence_ioc_code(self):
        country = fields.Country.country_from_ioc('XXX')
        self.assertIsNone(country)
