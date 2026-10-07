from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from questions.models import Category, ChoiceQuestion


class ChoiceQuestionAdminTests(TestCase):
    url = reverse("admin:questions_choicequestion_add")

    def setUp(self):
        admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="admin-pass-123"
        )
        self.client.force_login(admin)
        self.category = Category.objects.create(name="География")

    def post_question(self, correct_flags):
        data = {
            "category": self.category.pk,
            "text": "Коя е столицата на Франция?",
            "options-TOTAL_FORMS": len(correct_flags),
            "options-INITIAL_FORMS": 0,
            "options-MIN_NUM_FORMS": 4,
            "options-MAX_NUM_FORMS": 4,
        }
        for index, is_correct in enumerate(correct_flags):
            data[f"options-{index}-text"] = f"Отговор {index}"
            if is_correct:
                data[f"options-{index}-is_correct"] = "on"
        return self.client.post(self.url, data)

    def test_add_page_renders_four_option_forms(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="options-TOTAL_FORMS" value="4"')

    def test_valid_question_is_saved(self):
        response = self.post_question((False, True, False, False))

        self.assertEqual(response.status_code, 302)
        question = ChoiceQuestion.objects.get()
        self.assertEqual(question.options.filter(is_correct=True).count(), 1)

    def test_invalid_correct_answers_are_rejected(self):
        for flags in ((False, False, False, False), (True, True, False, False)):
            with self.subTest(flags=flags):
                response = self.post_question(flags)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "exactly one correct answer")
                self.assertFalse(ChoiceQuestion.objects.exists())
