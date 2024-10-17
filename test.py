# class EditProfileBaseView(NotAuthenticatedMixin, views.View):
#     success_url = 'index'
#     detailed_edit = False
#     model = UserModel
#
#     # TODO USE GET_QUERYSET
#
#     queryset = model.objects.select_related(
#         'profile__company'  # Fetch employee and company in one query
#     ).prefetch_related(
#         Prefetch(
#             'groups',
#             queryset=Group.objects.prefetch_related('permissions')),  # Prefetch permissions through groups
#         'user_permissions'  # Prefetch individual user permissions
#     )
#
#     def get_user_to_edit(self, slug):
#         # user_to_edit = self.queryset.filter(slug=slug).first()
#         # if not user_to_edit:
#         #     raise Http404("User not found")
#         user_to_edit = get_object_or_404(self.queryset, slug=slug)
#         return user_to_edit
#
#     @staticmethod
#     def _get_additional_form_class(detailed_edit=False):
#         form_class = DetailedEditProfileForm if detailed_edit else BasicEditProfileForm
#         return form_class
#
#     def get_success_url(self, slug, company_slug):
#         if company_slug:
#             return reverse("company members", kwargs={'company_slug': company_slug})
#         return reverse("profile", kwargs={'slug': slug})
#
#     def get_additional_form_class(self, detailed_edit):
#         try:
#             return self._get_additional_form_class(detailed_edit=detailed_edit)
#         except ValueError as e:
#             messages.error(self.request, str(e))
#             return None
#
#     def get_additional_form(self, user, request=None):
#         additional_form_class = self.get_additional_form_class(detailed_edit=self.detailed_edit)
#         if not additional_form_class:
#             return None
#
#         related_instance = user.profile
#
#         if request:
#             return additional_form_class(request.POST, instance=related_instance)
#         return additional_form_class(instance=related_instance)
#
#     @staticmethod
#     def get_context_data(user_form, additional_form, user, user_to_edit=None, company_slug=None):
#         return {
#             'user_form': user_form,
#             'additional_form': additional_form,
#             'user': user,
#             'user_to_edit': user_to_edit,
#             'company_slug': company_slug,
#         }
#
#     def form_valid(self, user_form, additional_form, user, user_to_edit=None):
#         try:
#             with transaction.atomic():
#                 user_form.save()
#                 if additional_form:
#                     additional_form.save()
#                 messages.success(self.request, 'Profile updated successfully.')
#                 return redirect(self.get_success_url(user.slug, user.company.slug))
#         except Exception as e:
#             logger.error(f"Error updating profile: {e}")
#             messages.error(self.request, "An unexpected error occurred while saving the profile.")
#             return self.form_invalid(user_form, additional_form, {})
#
#     def form_invalid(self, user_form, additional_form, context):
#         messages.error(self.request, 'Please correct the error below.')
#         return render(self.request, self.template_name, context)
#
#     def handle_form_loading_failure(self, user, user_to_edit=None):
#         logger.error(f"Failed to load forms for user {user_to_edit.email if user_to_edit else user.email}")
#         messages.error(self.request, "An unexpected error occurred. Please try again.")
#         return redirect(
#             self.get_success_url(slug=user.slug, company_slug=user.profile.company.slug))
#
#
# class BasicEditProfileView(OwnerRequiredMixin, EditProfileBaseView):
#     template_name = 'accounts/update_profile.html'
#     form_class = BasicEditTSPUserForm
#     success_url = 'profile'
#     detailed_edit = False
#
#     def get_success_url(self, slug, company_slug):
#         return reverse("profile", kwargs={'slug': slug})
#
#     def get(self, request, *args, **kwargs):
#         user = request.user
#         user_form = self.form_class(instance=user)
#         additional_form = self.get_additional_form(user)
#         if additional_form is None or user_form is None:
#             return self.handle_form_loading_failure(user)
#
#         context = self.get_context_data(user_form, additional_form, user)
#         return render(request, self.template_name, context)
#
#     def post(self, request, *args, **kwargs):
#         user = request.user
#         user_form = self.form_class(request.POST, instance=user)
#         additional_form = self.get_additional_form(user, request)
#         if additional_form is None or user_form is None:
#             return self.handle_form_loading_failure(user)
#
#         if user_form.is_valid() and (additional_form is None or additional_form.is_valid()):
#             return self.form_valid(user_form, additional_form, user, user)
#
#         context = self.get_context_data(user_form, additional_form, user)
#         return self.form_invalid(user_form, additional_form, context)
#
#
# class DetailedEditProfileView(PermissionRequiredMixin, DynamicPermissionMixin, EditProfileBaseView):
#     template_name = 'accounts/update_employee_profile.html'
#     form_class = DetailedEditTSPUserForm
#     success_url = 'company employee profile'
#     detailed_edit = True
#
#     def get_success_url(self, slug, company_slug):
#         return reverse("company members", kwargs={"company_slug": company_slug})
#
#     def dispatch(self, request, *args, **kwargs):
#         user = request.user
#         user_to_edit = self.get_user_to_edit(slug=self.kwargs['slug'])
#         permission = self.get_action_permission(user_to_edit, "change")
#         self.permission_required = permission
#         return super().dispatch(request, *args, **kwargs)
#
#     def get(self, request, *args, **kwargs):
#         user = request.user
#         user_to_edit = self.get_user_to_edit(slug=self.kwargs['slug'])
#         company_slug = user.profile.company.slug
#
#         user_form = self.form_class(instance=user_to_edit)
#         additional_form = self.get_additional_form(user_to_edit)
#
#         if additional_form is None or user_form is None:
#             return self.handle_form_loading_failure(user, user_to_edit)
#         context = self.get_context_data(user_form, additional_form, user, user_to_edit, company_slug)
#         return render(request, self.template_name, context)
#
#     def post(self, request, *args, **kwargs):
#         user = request.user
#         user_to_edit = self.get_user_to_edit(slug=self.kwargs['slug'])
#         company_slug = user.company.slug
#
#         user_form = self.form_class(request.POST or None, instance=user_to_edit)
#         additional_form = self.get_additional_form(user_to_edit, request)
#
#         if additional_form is None or user_form is None:
#             return self.handle_form_loading_failure(user, user_to_edit)
#
#         if user_form.is_valid() and (additional_form is None or additional_form.is_valid()):
#             return self.form_valid(user_form, additional_form, user, user_to_edit)
#
#         context = self.get_context_data(user_form, additional_form, user, user_to_edit, company_slug)
#         return self.form_invalid(user_form, additional_form, context)
#
#
# class DetailedOwnEditProfileView(OwnerRequiredMixin, DetailedEditProfileView):
#
#     template_name = 'accounts/full_update_own_profile.html'
#     form_class = DetailedEditTSPUserForm
#     detailed_edit = True
#
#     def get_success_url(self, slug, company_slug):
#         return reverse("profile", kwargs={"slug": slug})
#
#     def get_object(self, queryset=None):
#         return self.request.user