from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from questions.models import AnswerOption, Category, ChoiceQuestion, NumericQuestion


def create_choice_question(category, correct_flags=(True, False, False, False)):
    question = ChoiceQuestion.objects.create(category=category, text="Коя е столицата на България?")
    for index, is_correct in enumerate(correct_flags):
        AnswerOption.objects.create(question=question, text=f"Отговор {index}", is_correct=is_correct)
    return question


class CategoryTests(TestCase):
    def test_create_category(self):
        category = Category.objects.create(name="География")

        category.full_clean()
        self.assertEqual(str(category), "География")

    def test_name_is_unique(self):
        Category.objects.create(name="География")

        with self.assertRaises(ValidationError):
            Category(name="География").full_clean()
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="География")

    def test_category_with_questions_cannot_be_deleted(self):
        category = Category.objects.create(name="География")
        NumericQuestion.objects.create(category=category, text="Колко?", correct_answer=1)

        with self.assertRaises(ProtectedError):
            category.delete()
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())


class ChoiceQuestionTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="География")

    def test_create_valid_choice_question(self):
        question = create_choice_question(self.category)

        question.full_clean()
        self.assertEqual(question.category, self.category)
        self.assertEqual(question.options.count(), 4)
        self.assertEqual(question.options.filter(is_correct=True).count(), 1)
        self.assertIn(question, self.category.choicequestions.all())

    def test_invalid_choice_questions(self):
        cases = {
            "three options": (True, False, False),
            "five options": (True, False, False, False, False),
            "no correct answer": (False, False, False, False),
            "two correct answers": (True, True, False, False),
        }

        for name, flags in cases.items():
            with self.subTest(name):
                question = create_choice_question(self.category, flags)

                with self.assertRaises(ValidationError):
                    question.full_clean()

    def test_answer_option_rejects_fifth_option(self):
        question = create_choice_question(self.category)

        with self.assertRaises(ValidationError):
            AnswerOption(question=question, text="Пети", is_correct=False).full_clean()

    def test_answer_option_rejects_second_correct_answer(self):
        question = ChoiceQuestion.objects.create(category=self.category, text="Въпрос")
        AnswerOption.objects.create(question=question, text="А", is_correct=True)

        with self.assertRaises(ValidationError) as context:
            AnswerOption(question=question, text="Б", is_correct=True).full_clean()
        self.assertIn("is_correct", context.exception.message_dict)

    def test_deleting_question_deletes_answer_options(self):
        question = create_choice_question(self.category)

        question.delete()

        self.assertFalse(AnswerOption.objects.exists())


class NumericQuestionTests(TestCase):
    def test_create_numeric_question(self):
        category = Category.objects.create(name="Наука")

        question = NumericQuestion.objects.create(
            category=category, text="Колко планети има в Слънчевата система?", correct_answer=8
        )

        question.full_clean()
        self.assertEqual(question.correct_answer, 8)
        self.assertIn(question, category.numericquestions.all())

    def test_correct_answer_is_required_integer(self):
        category = Category.objects.create(name="Наука")

        for value in (None, "осем", "8.5"):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    NumericQuestion(category=category, text="Колко?", correct_answer=value).full_clean()
