import mimetypes
import os
from pathlib import Path
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsInstructor

from .models import Lecture
from .serializers import LectureListSerializer, LectureUploadSerializer
from .hls import is_safe_child_path
from .hls import transcode_to_hls


def _make_playback_token(*, lecture_id: int, user_id: int, token_version: int) -> str:
	payload = {
		'lecture_id': int(lecture_id),
		'user_id': int(user_id),
		'token_version': int(token_version),
	}
	return signing.dumps(payload, salt='lecture-playback')


def _unsign_playback_token(token: str) -> dict:
	max_age = getattr(settings, 'PLAYBACK_TOKEN_TTL_SECONDS', 60)
	return signing.loads(token, salt='lecture-playback', max_age=max_age)


def _unsign_hls_token(token: str) -> dict:
	max_age = getattr(settings, 'HLS_TOKEN_TTL_SECONDS', 300)
	return signing.loads(token, salt='lecture-playback', max_age=max_age)


_RANGE_RE = re.compile(r'^bytes=(\d+)-(\d*)$')


class LectureListCreateView(APIView):
	permission_classes = [IsAuthenticated]
	parser_classes = [MultiPartParser, FormParser]

	def get(self, request):
		lectures = Lecture.objects.order_by('-created_at')
		return Response(LectureListSerializer(lectures, many=True).data)

	def post(self, request):
		if not IsInstructor().has_permission(request, self):
			return Response({'detail': 'Instructor only'}, status=status.HTTP_403_FORBIDDEN)

		serializer = LectureUploadSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		lecture = serializer.save(uploaded_by=request.user)
		return Response(LectureListSerializer(lecture).data, status=status.HTTP_201_CREATED)


class LecturePlaybackView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, lecture_id: int):
		lecture = get_object_or_404(Lecture, id=lecture_id)
		token = _make_playback_token(
			lecture_id=lecture.id,
			user_id=request.user.id,
			token_version=request.user.token_version,
		)

		if lecture.hls_status == 'ready' and lecture.hls_manifest:
			playback_url = f"/api/lectures/{lecture.id}/hls/manifest/?token={token}"
			return Response({'playback_url': playback_url, 'expires_in_seconds': settings.HLS_TOKEN_TTL_SECONDS})

		playback_url = f"/api/lectures/{lecture.id}/stream/?token={token}"
		return Response({'playback_url': playback_url, 'expires_in_seconds': settings.PLAYBACK_TOKEN_TTL_SECONDS})


class LectureStreamView(APIView):
	"""Streams the lecture video after validating a short-lived signed token.

	This avoids exposing direct /media URLs and is the first step toward secure delivery.
	Supports HTTP Range requests for HTML5 video.
	"""

	authentication_classes = []
	permission_classes = []

	def get(self, request, lecture_id: int):
		token = request.query_params.get('token')
		if not token:
			return Response({'detail': 'Missing token'}, status=status.HTTP_401_UNAUTHORIZED)

		try:
			payload = _unsign_playback_token(token)
		except signing.SignatureExpired:
			return Response({'detail': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)
		except signing.BadSignature:
			return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

		if int(payload.get('lecture_id', -1)) != int(lecture_id):
			return Response({'detail': 'Token lecture mismatch'}, status=status.HTTP_401_UNAUTHORIZED)

		user_id = int(payload.get('user_id', -1))
		token_version = int(payload.get('token_version', -1))

		User = get_user_model()
		user = User.objects.filter(id=user_id).first()
		if user is None:
			return Response({'detail': 'Invalid user'}, status=status.HTTP_401_UNAUTHORIZED)
		if int(user.token_version) != token_version:
			return Response({'detail': 'Session expired (logged in elsewhere)'}, status=status.HTTP_401_UNAUTHORIZED)

		lecture = get_object_or_404(Lecture, id=lecture_id)
		if not lecture.video_file:
			raise Http404

		# Local filesystem path (works with default FileSystemStorage)
		try:
			file_path = lecture.video_file.path
		except NotImplementedError:
			return Response({'detail': 'Streaming not supported for this storage backend yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)

		content_type, _ = mimetypes.guess_type(file_path)
		content_type = content_type or 'application/octet-stream'

		file_size = os.path.getsize(file_path)
		range_header = request.META.get('HTTP_RANGE')
		if range_header:
			match = _RANGE_RE.match(range_header)
			if match:
				start = int(match.group(1))
				end_str = match.group(2)
				end = int(end_str) if end_str else file_size - 1
				end = min(end, file_size - 1)
				if start > end:
					return HttpResponse(status=416)

				length = end - start + 1
				f = open(file_path, 'rb')
				f.seek(start)

				response = HttpResponse(f.read(length), status=206, content_type=content_type)
				response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
				response['Accept-Ranges'] = 'bytes'
				response['Content-Length'] = str(length)
				return response

		response = FileResponse(open(file_path, 'rb'), content_type=content_type)
		response['Accept-Ranges'] = 'bytes'
		response['Content-Length'] = str(file_size)
		return response


class LectureHlsManifestView(APIView):
	authentication_classes = []
	permission_classes = []

	def get(self, request, lecture_id: int):
		token = request.query_params.get('token')
		if not token:
			return Response({'detail': 'Missing token'}, status=status.HTTP_401_UNAUTHORIZED)

		try:
			payload = _unsign_hls_token(token)
		except signing.SignatureExpired:
			return Response({'detail': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)
		except signing.BadSignature:
			return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

		if int(payload.get('lecture_id', -1)) != int(lecture_id):
			return Response({'detail': 'Token lecture mismatch'}, status=status.HTTP_401_UNAUTHORIZED)

		user_id = int(payload.get('user_id', -1))
		token_version = int(payload.get('token_version', -1))

		User = get_user_model()
		user = User.objects.filter(id=user_id).first()
		if user is None or int(user.token_version) != token_version:
			return Response({'detail': 'Session expired (logged in elsewhere)'}, status=status.HTTP_401_UNAUTHORIZED)

		lecture = get_object_or_404(Lecture, id=lecture_id)
		if lecture.hls_status != 'ready' or not lecture.hls_manifest:
			return Response({'detail': 'HLS not ready'}, status=status.HTTP_409_CONFLICT)

		manifest_path = Path(lecture.hls_manifest)
		if not manifest_path.exists():
			raise Http404

		# Rewrite segment URIs to point to our signed asset endpoint.
		lines = manifest_path.read_text(encoding='utf-8').splitlines()
		rewritten: list[str] = []
		for line in lines:
			if line and not line.startswith('#') and not line.startswith('http'):
				asset_url = f"/api/lectures/{lecture.id}/hls/asset/{line}?token={token}"
				rewritten.append(asset_url)
			else:
				rewritten.append(line)

		body = "\n".join(rewritten) + "\n"
		return HttpResponse(body, content_type='application/vnd.apple.mpegurl')


class LectureHlsAssetView(APIView):
	authentication_classes = []
	permission_classes = []

	def get(self, request, lecture_id: int, asset: str):
		token = request.query_params.get('token')
		if not token:
			return Response({'detail': 'Missing token'}, status=status.HTTP_401_UNAUTHORIZED)

		try:
			payload = _unsign_hls_token(token)
		except signing.SignatureExpired:
			return Response({'detail': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)
		except signing.BadSignature:
			return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

		if int(payload.get('lecture_id', -1)) != int(lecture_id):
			return Response({'detail': 'Token lecture mismatch'}, status=status.HTTP_401_UNAUTHORIZED)

		user_id = int(payload.get('user_id', -1))
		token_version = int(payload.get('token_version', -1))

		User = get_user_model()
		user = User.objects.filter(id=user_id).first()
		if user is None or int(user.token_version) != token_version:
			return Response({'detail': 'Session expired (logged in elsewhere)'}, status=status.HTTP_401_UNAUTHORIZED)

		lecture = get_object_or_404(Lecture, id=lecture_id)
		if lecture.hls_status != 'ready' or not lecture.hls_dir:
			return Response({'detail': 'HLS not ready'}, status=status.HTTP_409_CONFLICT)

		base_dir = Path(lecture.hls_dir)
		asset_path = base_dir / asset

		# Prevent path traversal
		if not is_safe_child_path(base_dir, asset_path):
			return Response({'detail': 'Invalid asset path'}, status=status.HTTP_400_BAD_REQUEST)
		if not asset_path.exists():
			raise Http404

		content_type, _ = mimetypes.guess_type(str(asset_path))
		content_type = content_type or 'application/octet-stream'

		return FileResponse(open(asset_path, 'rb'), content_type=content_type)


def watch_page(request):
	return render(request, 'watch.html')


def browse_page(request):
	return render(request, 'browse.html')


def upload_page(request):
	return render(request, 'upload.html')


# Minimal API endpoint to trigger HLS transcoding for a lecture (instructor only)
from rest_framework.decorators import api_view, permission_classes
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsInstructor])
def transcode_hls_api(request, lecture_id: int):
	lecture = get_object_or_404(Lecture, id=lecture_id)
	if not lecture.video_file:
		return Response({'detail': 'No video file'}, status=400)
	try:
		output_dir, manifest_path = transcode_to_hls(input_path=lecture.video_file.path, lecture_id=lecture.id)
		lecture.hls_dir = str(output_dir)
		lecture.hls_manifest = str(manifest_path)
		lecture.hls_status = 'ready'
		lecture.hls_error = ''
		lecture.save(update_fields=['hls_dir', 'hls_manifest', 'hls_status', 'hls_error'])
		return Response({'detail': 'HLS transcoding complete', 'manifest': lecture.hls_manifest})
	except Exception as e:
		lecture.hls_status = 'error'
		lecture.hls_error = str(e)
		lecture.save(update_fields=['hls_status', 'hls_error'])
		return Response({'detail': 'HLS transcoding failed', 'error': str(e)}, status=500)
