from django.db import models
from django.urls import reverse
from port.models import Teams, Chapters_Society_and_Affinity_Groups
from users.models import Members
# Create your models here.

class MeetingMinutes(models.Model):
    sc_ag = models.ForeignKey(Chapters_Society_and_Affinity_Groups, null=False, blank=False, on_delete=models.CASCADE)
    team = models.ForeignKey(Teams, null=True, blank=True, on_delete=models.SET_NULL)
    meeting_name = models.CharField(max_length=255, blank=False, null=False)
    location = models.CharField(max_length=50, blank=True, null=True)
    meeting_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, null=True)
    total_attendee = models.IntegerField(blank=False, null=False, default=0)
    ieee_attendee = models.IntegerField(blank=False, null=False, default=0)
    non_ieee_attendee = models.IntegerField(blank=False, null=False, default=0)
    agendas = models.JSONField(default=list)  
    discussion = models.TextField(blank=True, null=True)
    host = models.CharField(max_length=255, blank=True, null=True)
    co_host = models.CharField(max_length=255, blank=True, null=True)
    guest = models.CharField(max_length=255, blank=True, null=True)
    written_by = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.pk)
    
class MeetingMinutesAccess(models.Model):

    meeting_minutes = models.ForeignKey(MeetingMinutes, null=False, blank=False, on_delete=models.CASCADE)
    member = models.ForeignKey(Members, null=False, blank=False, on_delete=models.CASCADE)
    access_type = models.CharField(null=False, blank=False, max_length=20, choices=(('ViewOnly','ViewOnly'), ('Edit','Edit'), ('Restricted','Restricted')), default='Restricted')

    class Meta:
        verbose_name = 'Meeting Minutes Access'

    def __str__(self):
        return self.member.name