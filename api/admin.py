from django.contrib import admin
from .models import (
    Pmo,
    Profile,
    Notification,
    Organisation,
    HR,
    UserLoginActivity,
    SentEmailActivity,
    UserToken,
    CalendarEvent,
    Role,
    APILog,
    SuperAdmin,
    Finance,
    Sales,
    TableHiddenColumn,
    Tickets,
    Leader,
    Employee,
    UserRolePermissions,
    SubRole,
    TicketFeedback,
    StandardizedFieldRequest,
    StandardizedField
)



# Register your models here.

admin.site.register(Pmo)
admin.site.register(Organisation)
admin.site.register(HR)
admin.site.register(Profile)
admin.site.register(Notification)
admin.site.register(UserLoginActivity)
admin.site.register(SentEmailActivity)
admin.site.register(UserToken)
admin.site.register(CalendarEvent)
admin.site.register(Role)
admin.site.register(APILog)
admin.site.register(SuperAdmin)
admin.site.register(Finance)
admin.site.register(Sales)
admin.site.register(TableHiddenColumn)
admin.site.register(Leader)
admin.site.register(Tickets)
admin.site.register(UserRolePermissions)
admin.site.register(SubRole)
admin.site.register(TicketFeedback)
admin.site.register(StandardizedFieldRequest)
admin.site.register(StandardizedField)
admin.site.register(Employee)
