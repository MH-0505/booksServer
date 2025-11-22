from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Review


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


def update_book_average_rating(book):
    reviews = book.reviews.all()
    if reviews.exists():
        avg = round(sum(r.rating for r in reviews) / reviews.count(), 2)
        book.average_rating = avg
    else:
        book.average_rating = 0.0
    book.save(update_fields=['average_rating'])

@receiver(post_save, sender=Review)
def review_saved(sender, instance, **kwargs):
    update_book_average_rating(instance.book)

@receiver(post_delete, sender=Review)
def review_deleted(sender, instance, **kwargs):
    update_book_average_rating(instance.book)