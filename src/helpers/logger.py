import logging
import sys

class Logger(logging.Logger):
    def makeRecord(self, *args, **kwargs):
        rv = super(Logger, self).makeRecord(*args, **kwargs)
        rv.__dict__["chat_id"] = rv.__dict__.get("chat_id", "-")
        rv.__dict__["user_id"] = rv.__dict__.get("user_id", "-")
        return rv
    
def setup_logger():
    logger = Logger("logger")
    logger.propagate = False
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel("INFO")
    formatter=logging.Formatter("[%(asctime)s][%(filename)s:%(lineno)s - %(funcName)s()] [chat_id::%(chat_id)s] [user_id::%(user_id)s] %(levelname)s :: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger