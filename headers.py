from typing import Final

# This are the headers for the conversation between the clients, The sender and the receiver
MESSAGE_BEGIN: Final[str] = 'MSG_BEGIN'  # Signal for the beginning of the transfer
MESSAGE_END: Final[str] = 'MSG_END'  # Signal for the transfer ending, this is checked last
HEADER_BEGIN: Final[str] = 'HDR_BEGIN'  # The beginning of the headers ( the length and the hash check )
HEADER_END: Final[str] = 'HDR_END'  # Signal that the hash and massage length check was completed successful

# Number constance
SET_TIME: Final[float] = 0.5
DEFAULT_SIZE: Final[int] = 30
