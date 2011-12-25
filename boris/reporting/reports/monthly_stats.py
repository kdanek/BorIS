# -*- encoding: utf-8 -*-
'''
Created on 27.11.2011

@author: xaralis
'''
from django.db.models import Q
from django.utils.translation import ugettext as _

from boris.classification import SEXES, PRIMARY_DRUG_APPLICATION_TYPES, ANONYMOUS_TYPES,\
    DISEASES
from boris.clients.models import Town, District
from boris.reporting.core import Aggregation, Report,\
    SumAggregation, make_key, SuperAggregation, NonDistinctCountAggregation
from boris.reporting.models import SearchEncounter, SearchService

class EncounterAggregation(Aggregation): model = SearchEncounter
class ServiceAggregation(Aggregation):   model = SearchService


class AllClientEncounters(EncounterAggregation):
    title = _(u'Počet klientů')
    aggregation_dbcol = 'person'
    filtering = {'is_client': True}


class IvClientEncounters(AllClientEncounters):
    title = _(u'z toho injekčních uživatelů drog')
    filtering = {'is_client': True, 'primary_drug_usage': PRIMARY_DRUG_APPLICATION_TYPES.IV}


class MaleClientEncounters(AllClientEncounters):
    title = _(u'Z toho mužů')
    filtering = {'is_client': True, 'client_sex': SEXES.MALE}


class NonUserClientEncounters(AllClientEncounters):
    title = _(u'Z toho osob blízkých (sex. partneři)')
    filtering = {'is_client': True, 'primary_drug__isnull': True}


class NonClients(SuperAggregation):
    title = _(u'Počet neuživatelů, kteří využili alespoň jednou služeb programu')

    class AnonymousAggregation(NonDistinctCountAggregation, EncounterAggregation):
        aggregation_dbcol = 'person'
        filtering = {'is_anonymous': True}

    class PractitionerAggregation(EncounterAggregation):
        aggregation_dbcol = 'person'
        filtering = {'is_practitioner': True}

    aggregation_classes = (AnonymousAggregation, PractitionerAggregation)


class Parents(EncounterAggregation):
    aggregation_dbcol = 'person'
    title = _(u'Z toho rodiče')
    filtering = {
        'person__anonymous__drug_user_type': ANONYMOUS_TYPES.NON_USER_PARENT,
    }


class Practitioners(EncounterAggregation):
    aggregation_dbcol = 'person'
    title = _(u'Z toho odborná veřejnost')
    filtering = {'is_practitioner': True}


class AllAddresses(ServiceAggregation):
    title = _(u'Počet oslovených')
    aggregation_dbcol = 'id'
    filtering = {'content_type_model': 'address'}


class AddressesDU(AllAddresses):
    title = _(u'Z toho UD')
    filtering = (
        Q(content_type_model='address')
    ) & (
        Q(person__client__primary_drug__isnull=False) |
        Q(person__anonymous__drug_user_type__in=(ANONYMOUS_TYPES.IV,
            ANONYMOUS_TYPES.NON_IV))
    )


class AddressesNonDU(AllAddresses):
    title = _('Z toho neUD')
    filtering = (
        Q(content_type_model='address')
    ) & (
        (
            Q(is_client=True) & # the next atom is always True for anonyms
            Q(person__client__primary_drug__isnull=True)
        ) |
        Q(person__anonymous__drug_user_type__in=(ANONYMOUS_TYPES.NON_USER,
            ANONYMOUS_TYPES.NON_USER_PARENT))
    )


class DiseaseTestBase(ServiceAggregation):
    title = _(u'Počet testů VHC')
    filtering = {
        'content_type_model': 'diseasetest',
        'service__diseasetest__disease': DISEASES.VHC
    }

disease_tests = []

for key, title in DISEASES:
    attrs = {
        'title': _(u'Počet testů %s') % title,
        'filtering': {
            'content_type_model': 'diseasetest',
            'service__diseasetest__disease': key
        }
    }
    DiseaseTestClass = type(str('DiseaseTest%s' % title), (DiseaseTestBase,), attrs)
    disease_tests.append(DiseaseTestClass)


class EncounterCount(EncounterAggregation):
    title = _(u'Počet kontaktů celkem')


class ClientEncounterCount(ServiceAggregation):
    title = _(u'z toho s klienty, uživateli drog, přímý')
    aggregation_dbcol = 'encounter'
    filtering = {'is_client': True}
    excludes = {'content_type_model': 'phonecounseling'}


class PractitionerEncounterCount(EncounterCount):
    title = _(u'z toho s odbornou veřejností')
    filtering = {'is_practitioner': True}


class PhoneEncounterCount(ServiceAggregation):
    title = _(u'z toho telefonický kontakt')
    filtering = {'content_type_model': 'phonecounseling'}
    aggregation_dbcol = 'encounter'


class FirstContactCount(ServiceAggregation):
    title = _(u'Počet prvních kontaktů')
    filtering = (
        Q(is_client=True) &
        Q(content_type_model='incomeexamination')
    ) | (
        Q(is_anonymous=True) &
        Q(content_type_model='address')
    )


class FirstContactCountDU(FirstContactCount):
    title = _(u'z toho s UD')
    filtering = (
        Q(person__client__primary_drug__isnull=False) &
        Q(content_type_model='incomeexamination')
    ) | (
        Q(person__anonymous__drug_user_type__in=(ANONYMOUS_TYPES.IV, ANONYMOUS_TYPES.NON_IV)) &
        Q(content_type_model='address')
    )


class FirstContactCountIV(FirstContactCount):
    title = _(u'z toho nitrožilních UD')
    filtering = (
        Q(person__client__primary_drug_usage=PRIMARY_DRUG_APPLICATION_TYPES.IV) &
        Q(content_type_model='incomeexamination')
    ) | (
        Q(person__anonymous__drug_user_type=ANONYMOUS_TYPES.IV) &
        Q(content_type_model='address')
    )


class HarmReductionCount(ServiceAggregation):
    title = _(u'Počet výměn')
    filtering = {'content_type_model': 'harmreduction'}


class GatheredSyringes(SumAggregation, ServiceAggregation):
    title = _(u'Počet přijatého inj. materiálu')
    aggregation_dbcol = 'service__harmreduction__in_count'


class IssuedSyringes(SumAggregation, ServiceAggregation):
    title = _(u'Počet vydaného inj. materiálu')
    aggregation_dbcol = 'service__harmreduction__out_count'


class MonthlyStatsByTown(Report):
    title = _(u'Měsíční statistiky podle města')
    grouping = ('month', 'town')
    aggregation_classes = [
        AllClientEncounters,
        MaleClientEncounters,
        NonUserClientEncounters,
        IvClientEncounters,
        NonClients,
        Parents,
        Practitioners,
        AllAddresses,
        AddressesDU,
        AddressesNonDU,
    ] + disease_tests + [
        EncounterCount,
        ClientEncounterCount,
        PractitionerEncounterCount,
        PhoneEncounterCount,
        FirstContactCount,
        FirstContactCountDU,
        FirstContactCountIV,
        HarmReductionCount,
        GatheredSyringes,
        IssuedSyringes
    ]

    def _columns(self):
        if not hasattr(self, '_cols'):
            self._cols = [town for town in Town.objects.all()]
        return self._cols
    columns = property(_columns)

    def __init__(self, year, *args, **kwargs):
        self.year = year
        self.additional_filtering = {'year': year}
        super(MonthlyStatsByTown, self).__init__(*args, **kwargs)

    def months(self):
        return xrange(1, 13)

    def get_sum(self, aggregation, month):
        return sum(
            aggregation.get_val(make_key((('month', month), ('town', town.pk)),))
            for town in self.columns
        )

    def get_data(self):
        return [
            (month, [
                (aggregation.title, [
                    aggregation.get_val(
                        make_key((('month', month), ('town', town.pk)),)
                    ) for town in self.columns
                ] + [self.get_sum(aggregation, month)]) for aggregation in self.aggregations
            ]) for month in self.months()
        ]

class MonthlyStatsByDistrict(MonthlyStatsByTown):
    title = _(u'Měsíční statistiky podle okresu')
    grouping = ('month', 'town__district')

    def _columns(self):
        if not hasattr(self, '_cols'):
            self._cols = [district for district in District.objects.all()]
        return self._cols
    columns = property(_columns)

    def get_sum(self, aggregation, month):
        return sum(
            aggregation.get_val(make_key((('month', month), ('town__district', district.pk)),))
            for district in self.columns
        )

    def get_data(self):
        return [
            (month, [
                (aggregation.title, [
                    aggregation.get_val(
                        make_key((('month', month), ('town__district', district.pk)),)
                    ) for district in self.columns
                ] + [self.get_sum(aggregation, month)]) for aggregation in self.aggregations
            ]) for month in self.months()
        ]
