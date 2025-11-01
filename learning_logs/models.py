from django.db import models
from .mini_vader import MiniVader   

class Topic(models.Model):
    """A topic the user is learning about."""
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text


# class Entry(models.Model):
#     """Something specific learned about the topic."""
#     topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
#     text = models.TextField()  # ✅ changed from 'test' to 'text'
#     date_added = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         verbose_name_plural = 'entries'

#     def __str__(self):
#         """Return a simple string representing the entry."""
#         return f"{self.text[:50]}..."

class Entry(models.Model):
    """Something specific learned about a topic."""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    sentiment = models.CharField(max_length=20, default='neutral')  # positive / negative / neutral

    def save(self, *args, **kwargs):
        analyzer = MiniVader()
        self.sentiment = analyzer.analyze(self.text)  # returns label like "positive"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.text[:50]}... ({self.sentiment})"