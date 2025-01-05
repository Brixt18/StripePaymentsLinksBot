from enum import StrEnum


class HandleButtonsCommands(StrEnum):
    SELECT_PRODUCT = "select_product"

class HandleMessagesCommands(StrEnum):
    SELECTED_PRODUCT = "selected_product"