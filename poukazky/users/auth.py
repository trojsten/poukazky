from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from .models import User

ADMIN_OIDC_GROUP = "poukazky@iam.trojsten.sk"
ADMIN_DJANGO_GROUP = "admin"


def logout_url(request):
    return "https://id.trojsten.sk/oauth/logout"


class TrojstenID(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        uid = claims.get("sub")
        if not uid:
            return User.objects.none()
        return User.objects.filter(trojsten_id=uid)

    def create_user(self, claims):
        user = User()
        self._update_user(user, claims)
        user.save()

        return user

    def update_user(self, user, claims):
        self._update_user(user, claims)
        user.save()

        return user

    def _update_user(self, user, claims):
        user.trojsten_id = claims.get("sub")
        user.email = claims.get("email")
        user.username = claims.get("preferred_username")
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")

        oidc_groups = claims.get("groups", [])
        is_admin = ADMIN_OIDC_GROUP in oidc_groups
        user.is_staff = is_admin

        if is_admin:
            admin_group, _ = Group.objects.get_or_create(name=ADMIN_DJANGO_GROUP)
            user.save()  # when creating user, he will not exist at this time, so we need to save him.
            user.groups.add(admin_group)
