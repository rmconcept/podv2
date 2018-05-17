import os
import time
import datetime

from django.conf import settings
from django.core.files import File
from django.apps import apps
from django.utils import timezone
from webvtt import WebVTT, Caption
from pod.chapters.models import Chapter
if apps.is_installed('pod.authentication'):
    AUTH = True
if apps.is_installed('pod.filepicker'):
    FILEPICKER = True
    from pod.filepicker.models import CustomFileModel
    from pod.filepicker.models import UserDirectory


def chapter_to_vtt(list_chapter, video):
    webvtt = WebVTT()
    for chapter in list_chapter:
        start = datetime.datetime.utcfromtimestamp(
            chapter.time_start).strftime('%H:%M:%S.%f')[:-3]
        end = datetime.datetime.utcfromtimestamp(
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


def vtt_to_chapter(vtt, video):
    Chapter.objects.filter(video=video).delete()
    if FILEPICKER:
        webvtt = WebVTT().read(vtt.file.path)
    for caption in webvtt:
        time_start = time.strptime(caption.start.split('.')[0], '%H:%M:%S')
        time_start = datetime.timedelta(
            hours=time_start.tm_hour,
            minutes=time_start.tm_min,
            seconds=time_start.tm_sec).total_seconds()
        time_end = time.strptime(caption.end.split('.')[0], '%H:%M:%S')
        time_end = datetime.timedelta(
            hours=time_end.tm_hour,
            minutes=time_end.tm_min,
            seconds=time_end.tm_sec).total_seconds()

        if (time_start > video.duration or time_start < 0 or
                time_start > time_end):
            return 'The VTT file contains a chapter started at an ' + \
                   'incorrect time in the video : {0}'.format(caption.text)
        if time_end > video.duration or time_end < 0 or time_end < time_start:
            return 'The VTT file contains a chapter ended at an incorrect ' + \
                   'time in the video : {0}'.format(caption.text)
        Chapter.objects.create(
            video=video,
            title=caption.text,
            time_start=int(time_start),
            time_end=int(time_end))