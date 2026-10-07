from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class BaseQuestion(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="%(class)ss",
    )
    text = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.text


class ChoiceQuestion(BaseQuestion):
    REQUIRED_OPTIONS = 4

    @classmethod
    def validate_options(cls, options):
        """Checks a set of answer options (saved or not yet saved)."""
        errors = []
        if len(options) != cls.REQUIRED_OPTIONS:
            errors.append(
                ValidationError(
                    "A choice question must have exactly %(count)d answer options.",
                    code="options_count",
                    params={"count": cls.REQUIRED_OPTIONS},
                )
            )
        if sum(1 for option in options if option.is_correct) != 1:
            errors.append(
                ValidationError(
                    "A choice question must have exactly one correct answer.",
                    code="correct_count",
                )
            )
        if errors:
            raise ValidationError(errors)

    def clean(self):
        super().clean()
        # Answer options are attached after the question is saved,
        # so they can be validated only for existing questions.
        if self.pk:
            self.validate_options(list(self.options.all()))


class NumericQuestion(BaseQuestion):
    correct_answer = models.IntegerField()


class AnswerOption(models.Model):
    question = models.ForeignKey(
        ChoiceQuestion,
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    def clean(self):
        super().clean()
        if not self.question_id:
            return

        siblings = AnswerOption.objects.filter(question_id=self.question_id).exclude(
            pk=self.pk
        )
        if siblings.count() >= ChoiceQuestion.REQUIRED_OPTIONS:
            raise ValidationError(
                "A choice question cannot have more than %(count)d answer options.",
                code="options_count",
                params={"count": ChoiceQuestion.REQUIRED_OPTIONS},
            )
        if self.is_correct and siblings.filter(is_correct=True).exists():
            raise ValidationError(
                {"is_correct": "This question already has a correct answer."},
                code="correct_count",
            )
