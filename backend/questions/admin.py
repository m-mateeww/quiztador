from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import AnswerOption, Category, ChoiceQuestion, NumericQuestion


class AnswerOptionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        options = [
            form.instance
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        try:
            ChoiceQuestion.validate_options(options)
        except ValidationError as exc:
            raise ValidationError(exc.messages)


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    formset = AnswerOptionFormSet
    extra = 0  # min_num already renders the four required forms
    min_num = ChoiceQuestion.REQUIRED_OPTIONS
    max_num = ChoiceQuestion.REQUIRED_OPTIONS
    validate_min = True
    validate_max = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ChoiceQuestion)
class ChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "category")
    list_filter = ("category",)
    search_fields = ("text",)
    list_select_related = ("category",)
    inlines = [AnswerOptionInline]


@admin.register(NumericQuestion)
class NumericQuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "category", "correct_answer")
    list_filter = ("category",)
    search_fields = ("text",)
    list_select_related = ("category",)
