from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import Group


# class UserTypeMixin(models.Model):
#     class Meta:
#         abstract = True
#
#     def get_user_class_name(self):
#         return self.__class__.__name__
#
#     @property
#     def role(self):
#         return self.get_user_class_name()


class AbstractSlugMixin(models.Model):
    MAX_SLUG_LENGTH = 255

    class Meta:
        abstract = True

    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH,
        unique=True,
        null=False,
        blank=True,
        editable=False,
    )

    def save(self, *args, **kwargs):
        # super().save(*args, **kwargs)

        if not self.slug:
            self.slug = slugify(f"{self.get_slug_identifier()}")

        super().save(*args, **kwargs)

    def get_slug_identifier(self):
        raise NotImplementedError("Subclasses must implement this method")


class GroupAssignmentMixin(models.Model):
    user_field_name = 'user'  # Override in subclasses if the user field has a different name

    class Meta:
        abstract = True

    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        self.group = self.get_group()
        super().save(*args, **kwargs)
        self.add_user_to_group()

    def get_group(self):
        group_name = self.get_group_name()
        return Group.objects.get_or_create(name=group_name)[0]

    def get_group_name(self):
        raise NotImplementedError("Subclasses must implement 'get_group_name' method.")

    def add_user_to_group(self):
        user = getattr(self, self.user_field_name, None)
        if user is None:
            raise AttributeError(f"The model instance does not have a '{self.user_field_name}' attribute.")

        group_name = self.get_group_name()
        if not user.groups.filter(name=group_name).exists():
            user.groups.add(self.group)
            user.save()


