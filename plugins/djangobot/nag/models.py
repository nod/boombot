from django.db import models


class Event(models.Model):
    audience = models.CharField(maxlength=250)
    action = models.TextField()
    time = models.DateTimeField()


class Snooze(models.Model):
    event = models.ForeignKey(Event)
    sleep = models.IntegerField()
    expires = models.DateTimeField()


class Reminder(models.Model):
    event = models.ForeignKey(Event)
    method = models.CharField(maxlength=32)


class ReminderMeta(models.Model):
    reminder = models.ForeignKey('Reminder')
    metakey = models.SlugField()
    metavalue = models.TextField()


