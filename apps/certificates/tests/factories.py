"""Factories for certificates."""

import factory
from django.utils import timezone
from factory.fuzzy import FuzzyDecimal

from apps.certificates.models import Certificate, CertificateAccessLog
from apps.identification.tests.factories import IdentificationReportFactory
from apps.orders.tests.factories import StoneFactory


class CertificateFactory(factory.django.DjangoModelFactory):
    """Builds a certificate for a new stone and report."""

    class Meta:
        model = Certificate

    stone = factory.SubFactory(StoneFactory)
    report = factory.SubFactory(IdentificationReportFactory)
    certificate_number = factory.Sequence(lambda n: f"CERT-{n:05d}")
    verification_token = factory.Faker("uuid4")
    stone_type_snapshot = factory.Faker("word")
    weight_snapshot = FuzzyDecimal(0.5, 50, precision=3)
    issued_at = factory.LazyFunction(timezone.now)


class CertificateAccessLogFactory(factory.django.DjangoModelFactory):
    """Builds an access-log entry for a new certificate."""

    class Meta:
        model = CertificateAccessLog

    certificate = factory.SubFactory(CertificateFactory)
    ip_address = factory.Faker("ipv4")
