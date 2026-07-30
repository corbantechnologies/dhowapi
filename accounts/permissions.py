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

