from django.contrib import admin

from .models import Lecture


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'uploaded_by', 'created_at')
	search_fields = ('title',)

# Register your models here.
