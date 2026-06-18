"""Domain authorization for Blood Request actions (SDS 2.3.2 permission matrix).

Only Healthcare Professionals (role PROFESSIONAL) perform clinical actions, and
only for their own facility. Facility Administrators (role ADMIN) are explicitly
denied clinical actions and get read-only access elsewhere.
"""


class BloodRequestAuthorizer:
    def _is_professional(self, user) -> bool:
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "PROFESSIONAL"
            and user.facility_id is not None
        )

    def _is_requesting_facility(self, user, blood_request) -> bool:
        return self._is_professional(user) and (
            blood_request.requesting_facility_id == user.facility_id
        )

    def _is_fulfilling_facility(self, user, blood_request) -> bool:
        return self._is_professional(user) and (
            blood_request.fulfilling_facility_id == user.facility_id
        )

    # Fulfilling-facility actions
    def can_accept_request(self, user, blood_request) -> bool:
        return self._is_fulfilling_facility(user, blood_request)

    def can_reject_request(self, user, blood_request) -> bool:
        return self._is_fulfilling_facility(user, blood_request)

    def can_ship_request(self, user, blood_request) -> bool:
        return self._is_fulfilling_facility(user, blood_request)

    # Requesting-facility actions
    def can_receive_request(self, user, blood_request) -> bool:
        return self._is_requesting_facility(user, blood_request)

    def can_cancel_request(self, user, blood_request) -> bool:
        return self._is_requesting_facility(user, blood_request)
