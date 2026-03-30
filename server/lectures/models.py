from django.conf import settings
from django.db import models


class Lecture(models.Model):
	title = models.CharField(max_length=255)
	uploaded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='uploaded_lectures',
	)
	video_file = models.FileField(upload_to='lectures/')

	# HLS output (optional). Generated via management command.
	hls_dir = models.CharField(max_length=512, blank=True)
	hls_manifest = models.CharField(max_length=512, blank=True)
	hls_status = models.CharField(
		max_length=16,
		default='none',
		choices=[
			('none', 'None'),
			('processing', 'Processing'),
			('ready', 'Ready'),
			('failed', 'Failed'),
		],
	)
	hls_error = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.title
