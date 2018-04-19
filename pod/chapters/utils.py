from django.conf import settings
from django.core.files import File
from django.apps import apps
from django.utils import timezone
from webvtt import WebVTT, Caption
from datetime import datetime
if apps.is_installed('pod.authentication'):
    AUTH = True
    from pod.authentication.models import Owner
else:
    from django.contrib.auth.models import User
if apps.is_installed('pod.filepicker'):
    FILEPICKER = True
    from pod.filepicker.models import CustomFileModel
    from pod.filepicker.models import UserDirectory

import os


def chapter_to_vtt(list_chapter, video):
    webvtt = WebVTT()
    for chapter in list_chapter:
        start = datetime.utcfromtimestamp(
            chapter.time_start).strftime('%H:%M:%S.%f')[:-3]
        end = datetime.utcfromtimestamp(
            chapter.time_end).strftime('%H:%M:%S.%f')[:-3]
        caption = Caption(
            '{0}'.format(start),
            '{0}'.format(end),
            '{0}'.format(chapter.title))
        webvtt.captions.append(caption)
    if AUTH:
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            'files',
            video.owner.hashkey,
            'Home',
            'chapter_{0}.vtt'.format(video.title))
    else:
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            'files',
            video.owner.username,
            'Home',
            'chapter_{0}.vtt'.format(video.title))
    webvtt.save(file_path)
    file = File(open(file_path))
    file.name = 'chapter_{0}.vtt'.format(video.title)
    if FILEPICKER:
        home = UserDirectory.objects.get(
            owner=video.owner.user, name='Home')
        CustomFileModel.objects.filter(
            name='chapter_{0}'.format(video.title)).delete()
        CustomFileModel.objects.create(
            name='chapter_{0}'.format(video.title),
            file_size=os.path.getsize(file_path),
            file_type='VTT',
            date_created=timezone.now(),
            date_modified=timezone.now(),
            created_by=video.owner.user,
            modified_by=video.owner.user,
            directory=home,
            file=file)
        os.remove(file_path)
        path = os.path.join(
        	settings.MEDIA_URL, 
        	'files', 
        	video.owner.hashkey, 
        	'Home', 
        	file.name)
    else:
        path = os.path.join(
        	settings.MEDIA_URL, 
        	'files', 
        	video.owner.username, 
        	'Home', 
        	file.name)

    return path
