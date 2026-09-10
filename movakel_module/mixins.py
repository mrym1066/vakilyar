import jdatetime

class ShamsiDateMixin:
    @property
    def shamsi_date(self):
        if hasattr(self, 'date') and self.date:
            return jdatetime.date.fromgregorian(date=self.date).strftime('%Y/%m/%d')
        elif hasattr(self, 'meeting_date') and self.meeting_date:
            return jdatetime.date.fromgregorian(date=self.meeting_date).strftime('%Y/%m/%d')
        return "-"
