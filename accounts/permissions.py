from rest_framework.permissions import BasePermission

SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]


class IsDhowManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_dhow_manager
                or request.user.is_staff
                or request.user.is_superuser
            )
        )


class IsDhowManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_dhow_manager
                or request.user.is_staff
                or request.user.is_superuser
            )
        )


class IsGuest(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_guest
        )


class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_agent
        )


class IsSystemAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or (
                request.user.is_authenticated
                and (
                    request.user.is_dhow_manager
                    or request.user.is_staff
                    or request.user.is_superuser
                )
            )
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (
                request.user.is_authenticated
                and (
                    request.user.is_dhow_manager
                    or request.user.is_staff
                    or request.user.is_superuser
                )
            )
        )


class IsOwnerOrDhowManager(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if (
            request.user.is_dhow_manager
            or request.user.is_supervisor
            or request.user.is_staff
            or request.user.is_superuser
        ):
            return True
        booked_by = getattr(obj, "booked_by", None)
        created_by = getattr(obj, "created_by", None)
        user = getattr(obj, "user", None)
        paid_by = getattr(obj, "paid_by", None)
        return request.user in [booked_by, created_by, user, paid_by]


class IsSupervisor(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_supervisor
        )


class IsDhowManagerOrSupervisor(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_dhow_manager
                or request.user.is_supervisor
                or request.user.is_staff
                or request.user.is_superuser
            )
        )


class IsDhowManagerOrSupervisorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_dhow_manager
                or request.user.is_supervisor
                or request.user.is_staff
                or request.user.is_superuser
            )
        )



def is_system_admin(user):
    """Superusers and staff administer user accounts."""
    return bool(
        user and user.is_authenticated and (user.is_superuser or user.is_staff)
    )


class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsSelfOrSystemAdmin(BasePermission):
    """
    Users may view and edit their own account. System admins may view and edit
    any account. Dhow managers may view (not edit) any account.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if obj == request.user or is_system_admin(request.user):
            return True
        return request.method in SAFE_METHODS and request.user.is_dhow_manager
