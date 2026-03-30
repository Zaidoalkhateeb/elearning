from django.urls import path

from .views import (
    LectureHlsAssetView,
    LectureHlsManifestView,
    LectureListCreateView,
    LecturePlaybackView,
    LectureStreamView,
    transcode_hls_api,
)

urlpatterns = [
    path('', LectureListCreateView.as_view(), name='lecture_list_create'),
    path('<int:lecture_id>/playback/', LecturePlaybackView.as_view(), name='lecture_playback'),
    path('<int:lecture_id>/stream/', LectureStreamView.as_view(), name='lecture_stream'),
    path('<int:lecture_id>/hls/manifest/', LectureHlsManifestView.as_view(), name='lecture_hls_manifest'),
    path('<int:lecture_id>/hls/asset/<path:asset>', LectureHlsAssetView.as_view(), name='lecture_hls_asset'),
    path('<int:lecture_id>/transcode_hls/', transcode_hls_api, name='lecture_transcode_hls'),
]
