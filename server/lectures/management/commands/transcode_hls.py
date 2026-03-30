from django.core.management.base import BaseCommand, CommandError

from lectures.hls import transcode_to_hls
from lectures.models import Lecture


class Command(BaseCommand):
    help = "Transcode a Lecture's uploaded video into HLS (index.m3u8 + .ts segments)."

    def add_arguments(self, parser):
        parser.add_argument('lecture_id', type=int)

    def handle(self, *args, **options):
        lecture_id = int(options['lecture_id'])
        lecture = Lecture.objects.filter(id=lecture_id).first()
        if lecture is None:
            raise CommandError(f'Lecture {lecture_id} not found')
        if not lecture.video_file:
            raise CommandError('Lecture has no video_file')

        try:
            input_path = lecture.video_file.path
        except NotImplementedError:
            raise CommandError('This storage backend does not support local file paths')

        lecture.hls_status = 'processing'
        lecture.hls_error = ''
        lecture.save(update_fields=['hls_status', 'hls_error'])

        try:
            output_dir, manifest_path = transcode_to_hls(input_path=input_path, lecture_id=lecture.id)
        except Exception as exc:
            lecture.hls_status = 'failed'
            lecture.hls_error = str(exc)
            lecture.save(update_fields=['hls_status', 'hls_error'])
            raise CommandError(str(exc))

        lecture.hls_status = 'ready'
        lecture.hls_dir = str(output_dir)
        lecture.hls_manifest = str(manifest_path)
        lecture.hls_error = ''
        lecture.save(update_fields=['hls_status', 'hls_dir', 'hls_manifest', 'hls_error'])

        self.stdout.write(self.style.SUCCESS(f'HLS ready: {manifest_path}'))
