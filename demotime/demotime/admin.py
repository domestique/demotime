from django.contrib import admin

from demotime import models


class ReviewerInline(admin.TabularInline):
    model = models.Reviewer


class ReviewAdmin(admin.ModelAdmin):
    model = models.Review
    inlines = [ReviewerInline, ]

admin.site.register(models.Review, ReviewAdmin)
