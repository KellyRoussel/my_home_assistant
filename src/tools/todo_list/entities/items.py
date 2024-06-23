from datetime import datetime

class TodoItem:

    def __init__(self, importance: str, is_reminder_on: bool, status: str, title: str, created_date_time: datetime,
                 last_modified_date_time: datetime, has_attachments: bool, categories: list[str], id: str):
        self._importance = importance
        self._is_reminder_on = is_reminder_on
        self._status = status
        self._title = title
        self._created_date_time = created_date_time
        self._last_modified_date_time = last_modified_date_time
        self._has_attachments = has_attachments
        self._categories = categories
        self._id = id

    @classmethod
    def from_json(cls, json):
        try:
            return cls(
                json['importance'],
                json['isReminderOn'],
                json['status'],
                json['title'],
                datetime.strptime(json['createdDateTime'][:-2], '%Y-%m-%dT%H:%M:%S.%f'),
                datetime.strptime(json['lastModifiedDateTime'][:-2], '%Y-%m-%dT%H:%M:%S.%f'),
                json['hasAttachments'],
                json['categories'],
                json['id']
            )
        except Exception as e:
            raise Exception(f"{cls.__name__} : from_json: {e}")

    @property
    def importance(self):
        return self._importance

    @property
    def is_reminder_on(self):
        return self._is_reminder_on

    @property
    def status(self):
        return self._status

    @property
    def title(self):
        return self._title

    @property
    def created_date_time(self):
        return self._created_date_time

    @property
    def last_modified_date_time(self):
        return self._last_modified_date_time

    @property
    def has_attachments(self):
        return self._has_attachments

    @property
    def categories(self):
        return self._categories

    @property
    def id(self):
        return self._id

    def __str__(self):
        return self.title