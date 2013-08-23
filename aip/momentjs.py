from jinja2 import Markup


class momentjs(object):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def render(self, format):
        return Markup("<span class=momentjs data-format='%s'>%s</span>" % (format, self.timestamp.strftime("%Y-%m-%dT%H:%M:%S Z")))

    def format(self, fmt):
        return self.render(fmt)

    def calendar(self):
        return self.render("calendar")

    def fromNow(self):
        return self.render("fromNow")
