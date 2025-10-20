class BloodRequestAuthorizer:
    def _is_admin(self, user) -> bool:
        return bool(
            user and user.is_authenticated and getattr(user, "role", None) == "ADMIN"
        )

    def _is_requesting_facility(self, user, blood_request) -> bool:
        return bool(
            user
            and user.is_authenticated
            and user.facility
            and blood_request.requesting_facility == user.facility
        )

    def _is_fulfilling_facility(self, user, blood_request) -> bool:
        return bool(
            user
            and user.is_authenticated
            and user.facility
            and blood_request.fulfilling_facility == user.facility
        )

    def can_accept_request(self, user, blood_request) -> bool:
        return self._is_admin(user) or self._is_fulfilling_facility(user, blood_request)

    def can_reject_request(self, user, blood_request) -> bool:
        return self.can_accept_request(user, blood_request)

    def can_ship_request(self, user, blood_request) -> bool:
        return self.can_accept_request(user, blood_request)

    def can_receive_request(self, user, blood_request) -> bool:
        return self._is_admin(user) or self._is_requesting_facility(user, blood_request)

    def can_cancel_request(self, user, blood_request) -> bool:
        return self.can_receive_request(user, blood_request)
