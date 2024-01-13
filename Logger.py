import logging
from ModuleBase import Module
from pubsub import pub
import datetime
# from ratelimitingfilter import RateLimitingFilter

class Logger(Module):

    def __init__(self, log_file, log_print, rate_limiter = None, *args):

        logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")
        self.rootLogger = logging.getLogger()
        self.rootLogger.setLevel(logging.DEBUG)

        # RATE LIMITER FILTER - LOGGING
        if rate_limiter is not None:
            self.rate = rate_limiter

        if log_file:
            log_date = datetime.datetime.now()
            log_date = log_date.strftime("%x").replace("/", "-")
            fileHandler = logging.FileHandler(f"./logs/{log_date}.log", mode = "a")
            fileHandler.setFormatter(logFormatter)
            self.rootLogger.addHandler(fileHandler)

        if log_print:
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logFormatter)
            self.rootLogger.addHandler(consoleHandler)

        for topic in args:
            if rate_limiter:

                topic_logger = topic.replace(".", "_")
                exec(f"{topic_logger} = TopicLogger('{topic}', {self.rate})")

            else:
                pub.subscribe(self.listener, topic)

    def listener(self, message):
        self.rootLogger.debug(f"{message}")


class TopicLogger(Module):

    def __init__(self, topic, freq):
        self.topic = topic
        self.new_message = None
        self.logged_message = None
        self.rootLogger = logging.getLogger()
        self.freq = freq
        pub.subscribe(self.listener, topic)

        self.start(freq)

    def listener(self, message):
        self.new_message = message

    def run(self):
        if self.logged_message is not self.new_message:
            self.rootLogger.debug(f"{self.new_message}")
            self.logged_message = self.new_message

if __name__ == "__main__":
    pass
