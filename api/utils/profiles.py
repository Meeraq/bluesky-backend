from api.models import (
    Pmo,
    SuperAdmin,
    Finance,
    Sales,
    Leader,
    HR,
    Employee
)

from zohoapi.models import Vendor

model_mapping = {
    "pmo": Pmo,
    "superadmin": SuperAdmin,
    "finance": Finance,
    "sales": Sales,
    "leader": Leader,
    "hr": HR,
    "employee": Employee,
    "vendor": Vendor,
}


def update_profiles_active_inactive(profile, active_inactive):
    if profile and profile.roles.all().exists():
        print("inside if")
        for role in profile.roles.all():
            print(role.name)
            try:
                # Fetch the model class based on the role name and update its active_inactive field
                model_class = model_mapping.get(role.name)
                if model_class:
                    print(
                        "updating active inactive",
                        active_inactive,
                        model_class.objects.filter(user=profile),
                    )
                    model_class.objects.filter(user=profile).update(
                        active_inactive=active_inactive
                    )
                else:
                    print(f"Role {role.name} does not have a corresponding model.")
            except Exception as e:
                print(f"Error updating {role.name}: {str(e)}")
