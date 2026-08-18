from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Role

from .models import AuditLog
from .services import record


User = get_user_model()


class AuditLogTests(TestCase):
    def test_logs_are_immutable_and_do_not_store_request_bodies(self):
        role = Role.objects.get(name=Role.Name.STUDENT)
        actor = User.objects.create_user(email="audit@example.com", name="Audit", password="ComplexPass123!", role=role)
        log = record(actor=actor, action=AuditLog.Action.PLAN_GENERATED, description="Generated study plan #1.")
        self.assertEqual(log.description, "Generated study plan #1.")
        with self.assertRaises(TypeError):
            AuditLog.objects.filter(pk=log.pk).update(description="Changed")
        with self.assertRaises(TypeError):
            log.delete()
