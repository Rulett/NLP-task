import enum


class TaskStatusEnum(enum.Enum):
    """
    Define the statuses for audio processing tasks.

    Attributes:
        PENDING (str): The task is waiting to be processed.
        STARTED (str): The task has started processing.
        SUCCESS (str): The task has been successfully completed.
        FAILURE (str): The task has failed during processing.
    """

    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
