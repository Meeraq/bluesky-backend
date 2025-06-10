from django.urls import path, include
from . import views
from .views import (
    TicketNumberGenerateView,
    UserTokenAvaliableCheck,
    UpdateUserRoles,
    UniqueValuesView,
    GetModelOptionsView,
    TicketListCreateView,
    TicketStatisticsAPIView,
    TicketRetrieveUpdateDestroyView,
    AllTicketListView,
    AddCommentView,
    UserRolePermissionsListCreateView,
    UserRolePermissionsRetrieveUpdateDestroyView,
    SubRoleListCreateView,
    SubRoleRetrieveUpdateDestroyView,
    RoleListCreateView,
    RoleRetrieveUpdateDestroyView,
)

urlpatterns = [
    path("pmos/", views.create_pmo),
    path(
        "password_reset/",
        include("django_rest_passwordreset.urls", namespace="password_reset"),
    ),
    path("management-token/", views.get_management_token),
    path("hr/all/", views.get_hr),
    path("csrf/", views.get_csrf, name="api-csrf"),
    path("login/", views.login_view, name="api-login"),
    path("logout/", views.logout_view, name="api-logout"),
    path("session/", views.session_view, name="api-session"),
    path("otp/generate/", views.generate_otp),
    path("otp/validate/", views.validate_otp),
    path("change-user-role/<int:user_id>/", views.change_user_role),
    path("users/", views.get_users),
    path("add_hr/", views.add_hr),
    path("add_organisation/", views.add_organisation),
    path("get_organisation/", views.get_organisation),
    path("notifications/all/<int:user_id>/", views.get_notifications),
    path("notifications/mark-as-read/", views.mark_notifications_as_read),
    path("notifications/mark-all-as-read/", views.mark_all_notifications_as_read),
    path("notifications/unread-count/<int:user_id>/", views.unread_notification_count),
    path("update_organisation/<int:org_id>/", views.update_organisation),
    path("update_hr/<int:hr_id>/", views.update_hr),
    path("microsoft/oauth/<str:user_mail_address>/", views.microsoft_auth),
    path("microsoft-auth-callback/", views.microsoft_callback),
    path(
        "user-token-avaliable-check/<str:user_mail>/",
        UserTokenAvaliableCheck.as_view(),
    ),
    path("logs/", views.get_api_logs, name="get_api_logs"),
    path("edit-pmo/", views.edit_pmo),
    path("update-user-roles/", UpdateUserRoles.as_view()),
    path("v2/filter-options/", UniqueValuesView.as_view()),
    path(
        "v2/get-model-options/", GetModelOptionsView.as_view(), name="get_model_options"
    ),
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list-create"),
    path(
        "tickets/statistics/",
        TicketStatisticsAPIView.as_view(),
        name="ticket-statistics",
    ),
    path(
        "get-ticket-number/",
        TicketNumberGenerateView.as_view(),
        name="generate-ticket-number",
    ),
    path(
        "tickets/<int:pk>/",
        TicketRetrieveUpdateDestroyView.as_view(),
        name="ticket-retrieve-update-destroy",
    ),
    path(
        "tickets/all/",
        AllTicketListView.as_view(),
    ),
    path(
        "tickets/feedback/<uuid:unique_id>/",
        views.TicketFeedbackAPIView.as_view(),
        name="ticket-feedback-api",
    ),
    path("comments/", AddCommentView.as_view(), name="add-comment"),
    # Event URLs
    path(
        "user-role-permissions/",
        UserRolePermissionsListCreateView.as_view(),
        name="user-role-permissions-list-create",
    ),
    path(
        "user-role-permissions/<int:pk>/",
        UserRolePermissionsRetrieveUpdateDestroyView.as_view(),
        name="user-role-permissions-detail",
    ),
    path("sub-roles/", SubRoleListCreateView.as_view(), name="sub-role-list-create"),
    path(
        "roles/<str:role_name>/sub-roles/",
        views.GetSubRolesForRole.as_view(),
        name="sub-role-list-create",
    ),
    path(
        "role/<str:role_name>/",
        views.GetRoleForName.as_view(),
        name="role-list",
    ),
    path(
        "sub-roles/<int:pk>/",
        SubRoleRetrieveUpdateDestroyView.as_view(),
        name="sub-role-detail",
    ),
    path("roles/", RoleListCreateView.as_view(), name="role-list-create"),
    path(
        "roles/<int:pk>/", RoleRetrieveUpdateDestroyView.as_view(), name="role-detail"
    ),
    path(
        "user-role-permissions-of-subrole/<int:role>/<int:sub_role>/",
        views.UserRolePermissionsRetrieveView.as_view(),
        name="user-role-permissions-retrieve",
    ),
    path(
        "roles/p/",
        views.RoleListCreateViewPagination.as_view(),
        name="role-list-create",
    ),
    path(
        "get-team-of-manager/",
        views.GetTeamOfManager.as_view(),
        name="team-of-manager",
    ),
    path(
        "get-permission-of-user-role/<str:user_type>/<int:user_id>/",
        views.GetPermissionForUserRole.as_view(),
        name="get-permission-of-user-role",
    ),
    path(
        "update-sub-role-of-user/",
        views.UpdateSubRoleOfUser.as_view(),
        name="update-sub-role-of-user",
    ),
    path("standard_field/<int:user_id>/", views.standard_field_request),
    path("standardized-fields/", views.StandardizedFieldAPI.as_view()),
    path("standardized-field-requests/", views.StandardizedFieldRequestAPI.as_view()),
    path("standard-field-add-value/", views.StandardFieldAddValue.as_view()),
    path("standard-field-edit-value/", views.StandardFieldEditValue.as_view()),
    path(
        "standardized-field-request-accept-reject/",
        views.StandardizedFieldRequestAcceptReject.as_view(),
    ),
    path("standard-field-delete-value/", views.StandardFieldDeleteValue.as_view()),
    path(
        "active-deligation-for-user/<int:user_id>/<str:user_type>/<str:status>/",
        views.ActiveDeligationOfUser.as_view(),
        name="active-deligation-for-user",
    ),
    path(
        "active-deligation-for-user-depth/<int:user_id>/<str:user_type>/<str:status>/",
        views.ActiveDeligationOfUserDepth.as_view(),
        name="active-deligation-for-user-depth",
    ),
    path(
        "deligated-user-role-permissions/<int:employee_id>/",
        views.DeligatedToRolePermission.as_view(),
        name="deligated-user-role-permissions",
    ),
    path("v2/delete-gmsheet/", views.DeleteGmSheetView.as_view()),
    path("v2/all-gmsheet/", views.AllGmSheetView.as_view()),
    path("all-gmsheet/", views.get_all_gmsheet),
    path("v2/offerings/<int:gmsheet_id>/", views.OfferingsByGMSheetView.as_view()),
    path(
        "v2/gmsheet-by-sales/<int:sales_person_id>", views.GMSheetBySalesView.as_view()
    ),
    path("v2/create-employee/", views.CreateEmployeeView.as_view()),
    path("v2/employees/", views.GetEmployeeListView.as_view()),
    path("v2/update-employee/", views.EmployeeUpdateView.as_view()),
    path("update-employee/", views.update_employee, name="update_employee"),
    path("v2/delete-employee/", views.DeleteEmployeeView.as_view()),
    path(
        "v2/leader-cumulative-data/",
        views.LeaderCumulativeDataView.as_view(),
        name="leader-cumulative-data",
    ),
    path("get-benchmark/", views.get_all_benchmarks),
    path(
        "user-hierarchy/",
        views.UserHierarchyListCreateView.as_view(),
        name="user-hierarchy-list-create",
    ),
    path(
        "user-hierarchy/<int:pk>/",
        views.UserHierarchyRetrieveUpdateDestroyView.as_view(),
        name="user-hierarchy-detail",
    ),
    path(
        "user-hierarchy/employee/<int:user_id>/",
        views.UserHierarchyRetrieveAPIView.as_view(),
        name="user-hierarchy-by-user",
    ),
    path(
        "user-hierarchy/user/<int:user_id>/",
        views.UserHierarchyOfUserRetrieveAPIView.as_view(),
        name="user-hierarchy-by-user",
    ),
    # Hierarchy Change endpoints
    path(
        "hierarchy-changes/<int:user_id>/",
        views.HierarchyChangeListAPIView.as_view(),
        name="hierarchy-changes-list",
    ),
    path(
        "hierarchy-changes/",
        views.HierarchyChangeListAPIView.as_view(),
        name="hierarchy-changes-all",
    ),
    # Supervisor endpoints
    path(
        "potential-supervisors/<int:employee_id>/",
        views.PotentialSupervisorsAPIView.as_view(),
        name="potential-supervisors",
    ),
    # User Delegation endpoints
    path(
        "user-delegations/",
        views.UserDelegationListCreateView.as_view(),
        name="user-delegation-list-create",
    ),
    path(
        "user-delegations/<int:pk>/",
        views.UserDelegationRetrieveUpdateDestroyView.as_view(),
        name="user-delegation-detail",
    ),
    path(
        "record-delegation-action/",
        views.RecordDelegationAction.as_view(),
        name="record-delegation-action",
    ),
    # Delegation History endpoints
    path(
        "delegation-history/",
        views.DelegationHistoryListView.as_view(),
        name="delegation-history-list",
    ),
    path(
        "delegation-history/<int:pk>/",
        views.DelegationHistoryDetailView.as_view(),
        name="delegation-history-detail",
    ),
    # Organization structure endpoint
    path(
        "organization-structure/",
        views.OrganizationStructureAPIView.as_view(),
        name="organization-structure",
    ),
    path("employees/", views.get_employees, name="get_employees"),
    path("create-employee/", views.create_employee, name="employee-create"),
    path("v2/hr-and-organisation/all/", views.HrAndOrganisationView.as_view()),
    path("create-gmsheet/", views.create_gmsheet, name="create_gmsheet"),
    path(
        "offerings/<int:gmsheet_id>/",
        views.get_offerings_by_gmsheet_id,
        name="offerings-list",
    ),
    path("gmsheet/<int:id>/offerings/add/", views.add_offerings),
    path("update-gmsheet/<int:id>/", views.update_gmsheet),
    path(
        "accept-gmsheet/<int:pk>/",
        views.update_is_accepted_status,
        name="update_is_accepted_status",
    ),
    path("create-benchmark/", views.create_benchmark, name="create_benchmark"),
    path("update-benchmark/", views.update_benchmark, name="update_benchmark"),
]
