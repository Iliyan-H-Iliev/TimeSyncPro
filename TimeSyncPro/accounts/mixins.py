from django.db import models
from django.utils.text import slugify
# from django.contrib.auth.models import Group


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
        if not self.slug:
            temp_slug = slugify(f"{self.get_slug_identifier()}")
            self.slug = temp_slug[:self.MAX_SLUG_LENGTH]

        # Check if this is a new instance (no pk) or if the slug hasn't been modified
        if not self.pk or not self._state.adding:
            super().save(*args, **kwargs)

            try:
                has_attr_first_name = bool(getattr(self, 'first_name'))
            except AttributeError:
                has_attr_first_name = False

            # Only add the pk to the slug for models with 'first_name' attribute
            if has_attr_first_name and self.pk:
                current_slug = self.slug
                new_slug = f"{current_slug}-{self.pk}"
                if len(new_slug) <= self.MAX_SLUG_LENGTH and not current_slug.endswith(f"-{self.pk}"):
                    self.slug = new_slug
                    # Use update() to avoid triggering the save method again
                    type(self).objects.filter(pk=self.pk).update(slug=new_slug)
        else:
            super().save(*args, **kwargs)

    def get_slug_identifier(self):
        raise NotImplementedError("Subclasses must implement this method")


# class GroupAssignmentMixin(models.Model):
#     user_field_name = 'user'  # Override in subclasses if the user field has a different name
#
#     class Meta:
#         abstract = True
#
#     group = models.ForeignKey(
#         Group,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#     )
#
#     def save(self, *args, **kwargs):
#         self.group = self.get_group()
#         super().save(*args, **kwargs)
#         self.add_user_to_group()
#
#     def get_group(self):
#         group_name = self.get_group_name()
#         return Group.objects.get_or_create(name=group_name)[0]
#
#     def get_group_name(self):
#         raise NotImplementedError("Subclasses must implement 'get_group_name' method.")
#
#     def add_user_to_group(self):
#         user = getattr(self, self.user_field_name, None)
#         if user is None:
#             raise AttributeError(f"The model instance does not have a '{self.user_field_name}' attribute.")
#
#         group_name = self.get_group_name()
#         if not user.groups.filter(name=group_name).exists():
#             user.groups.add(self.group)
#             user.save()
#

