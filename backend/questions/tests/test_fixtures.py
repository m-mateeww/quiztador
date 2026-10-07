from django.db.models import Count, Q
from django.test import TestCase

from questions.models import AnswerOption, Category, ChoiceQuestion, NumericQuestion


class QuestionBankFixtureTests(TestCase):
    fixtures = ["questions/question_bank.json"]

    def test_fixture_counts(self):
        self.assertEqual(Category.objects.count(), 6)
        self.assertEqual(ChoiceQuestion.objects.count(), 12)
        self.assertEqual(AnswerOption.objects.count(), 48)
        self.assertEqual(NumericQuestion.objects.count(), 12)

    def test_every_choice_question_is_valid(self):
        questions = ChoiceQuestion.objects.annotate(
            option_count=Count("options"),
            correct_count=Count("options", filter=Q(options__is_correct=True)),
        )

        for question in questions:
            with self.subTest(question=question.pk):
                self.assertEqual(question.option_count, 4)
                self.assertEqual(question.correct_count, 1)
                question.full_clean()

    def test_every_numeric_question_has_integer_answer(self):
        for question in NumericQuestion.objects.all():
            with self.subTest(question=question.pk):
                self.assertIsInstance(question.correct_answer, int)
                question.full_clean()
