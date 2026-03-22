class VWClientError(RuntimeError):
    pass


class AuthenticationError(VWClientError):
    pass


class VehicleSessionError(VWClientError):
    pass
