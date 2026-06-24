"""Domain authorization for Blood Request actions (least-privilege; ADR-0008).

Clinical work is split across two roles, each scoped to its own facility:

- SUPPLY fulfills incoming requests for their facility: accept, reject, ship.
- CLINICIAN raises and tracks outgoing requests: create, cancel, receive.

ADMIN performs no clinical actions (user/facility management + read-only).
"""


class BloodRequestAuthorizer:
    def _has_role(self, user, role) -> bool:
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == role
            and user.facility_id is not None
        )

    def _is_supply_for(self, user, blood_request) -> bool:
        return self._has_role(user, "SUPPLY") and (
            blood_request.fulfilling_facility_id == user.facility_id
        )

    def _is_clinician_for(self, user, blood_request) -> bool:
        return self._has_role(user, "CLINICIAN") and (
            blood_request.requesting_facility_id == user.facility_id
        )

    # Fulfilling-facility actions (SUPPLY)
    def can_accept_request(self, user, blood_request) -> bool:
        return self._is_supply_for(user, blood_request)

    def can_reject_request(self, user, blood_request) -> bool:
        return self._is_supply_for(user, blood_request)

    def can_ship_request(self, user, blood_request) -> bool:
        return self._is_supply_for(user, blood_request)

    # Requesting-facility actions (CLINICIAN)
    def can_receive_request(self, user, blood_request) -> bool:
        return self._is_clinician_for(user, blood_request)

    def can_cancel_request(self, user, blood_request) -> bool:
        return self._is_clinician_for(user, blood_request)
