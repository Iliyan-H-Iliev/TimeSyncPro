from django.forms import SelectMultiple
from django.db import transaction
from django.shortcuts import render, redirect
from ..models import Shift, ShiftBlock
from django.db.models import F, Max

from ... import settings


class Select2SlideCheckboxWidget(SelectMultiple):
    class Media:
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
            )
        }
        js = (
            'https://code.jquery.com/jquery-3.7.1.min.js',
            'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
        )


# class CreateShiftBlocksMixin:
#
#     @staticmethod
#     def clear_shift_blocks_selected_days(shift):
#         blocks = shift.blocks.all()
#         for block in blocks:
#             block.selected_days = []
#             block.save()
#
#     def has_consistent_block_type(self, form, formset):
#         blocks_set = set()
#         for block in formset:
#             week_days = block.cleaned_data.get('week_days')
#             if week_days:
#                 blocks_set.add("selected_days")
#             else:
#                 blocks_set.add("days_on_days_off")
#         if len(blocks_set) > 1:
#             form.add_error(None, "All blocks must have the same type.")
#             return False
#         return True
#
#     def is_duplicate_name(form, shift, is_edit=False):
#         company = shift.company
#         name = form.cleaned_data['name']
#
#         if is_edit:
#             if Shift.objects.filter(company=company, name=name).exclude(pk=shift.pk).exists():
#                 form.add_error('name', 'Shift pattern with this name already exists for your company.')
#                 return True
#         else:
#             if Shift.objects.filter(company=company, name=name).exists():
#                 form.add_error('name', 'Shift pattern with this name already exists for your company.')
#                 return True
#
#         return False
#
#     def save_shift_blocks(formset, shift):
#         with transaction.atomic():
#             # Get the maximum existing order for this shift
#             max_order = ShiftBlock.objects.filter(pattern=shift).aggregate(Max('order'))['order__max'] or 0
#
#             blocks_to_create = []
#
#             for index, form in enumerate(formset, start=1):
#                 if form.is_valid() and not form.cleaned_data.get('DELETE'):
#                     block = form.save(commit=False)
#                     block.pattern = shift
#                     block.order = max_order + index
#                     blocks_to_create.append(block)
#
#             ShiftBlock.objects.bulk_create(blocks_to_create)
#
#     def validate_days_on_off_in_shift(form, combined_shift_blocks):
#         has_day_on = False
#         has_days_off = False
#
#         for block in combined_shift_blocks:
#
#             if not block.instance.on_off_days:
#                 form.add_error(None, "Shift pattern must have days on and days off.")
#                 return False
#
#             for day in block.instance.on_off_days:
#                 if day == 0:
#                     has_days_off = True
#                 else:
#                     has_day_on = True
#
#                 if has_day_on and has_days_off:
#                     break
#
#             if has_day_on and has_days_off:
#                 break
#
#         if not has_days_off or not has_day_on:
#             form.add_error(None, "Shift pattern must have working days and rest days.")
#             return False
#         return True
#
#     def validate_shift_start_date(form, shift, formset):
#         has_selected_days = True
#
#         for block in formset:
#             selected_days = block.cleaned_data.get('week_days')
#             if not selected_days:
#                 has_selected_days = False
#                 break
#
#         if has_selected_days:
#             start_date = shift.start_date
#             if start_date.weekday() != 0:
#                 form.add_error('start_date', 'Start date must be a Monday.')
#                 return False
#             return True
#
#         return True
#
#     def delete_shift_blocks(shift, is_existing):
#         if is_existing:
#             shift.blocks.all().delete()
#
#         shift.save()
#
#     def clear_deleted_blocks(formset):
#         new_forms = []
#         for i, form in enumerate(formset):
#             if hasattr(formset, 'cleaned_data') and formset.cleaned_data[i].get('DELETE', False):
#                 continue  # Skip forms marked for deletion
#             new_forms.append(form)
#         return new_forms
#
#     def check_formset_forms_quantity(formset, company):
#
#         if len(formset) == 0:
#             formset.add_error(None, "You must have at least one block.")
#             redirect("all_shifts", kwargs={'company_slug': company.slug, "error": "You must have at least one block."})
#         return True
#
#     @transaction.atomic
#     def handle_shift_post(request, form, formset, pk, company, template_name, redirect_url, *args, **kwargs):
#
#         context = {
#             'form': form,
#             'formset': formset,
#             'company_slug': company.slug,
#             'pk': pk
#         }
#
#         obj = kwargs.get('obj', None)
#
#         if obj:
#             context['object'] = obj
#
#         with transaction.atomic():
#             try:
#
#                 with transaction.atomic():
#                     try:
#                         shift = form.save(commit=False)
#
#                         formset = clear_deleted_blocks(formset)
#
#                         # combined_shift_blocks = retrieve_combined_shift_blocks(formset, shift, is_edit=bool(pk))
#                         shift.company = company
#                         formset_quantity = check_formset_forms_quantity(formset, company)
#                         is_duplicate = is_duplicate_name(form, shift, is_edit=bool(pk))
#                         has_consistent = has_consistent_block_type(form, formset)
#                         has_days_off = validate_days_on_off_in_shift(form, formset)
#                         check_start_date = validate_shift_start_date(form, shift, formset)
#
#                         if is_duplicate or not has_consistent or not has_days_off or not check_start_date or not formset_quantity:
#                             return render(request, template_name, context)
#
#                         delete_shift_blocks(shift, is_existing=bool(pk))
#                         save_shift_blocks(shift=shift, formset=formset)
#                     except Exception as e:
#                         form.add_error(None, f"An unexpected error please try again:")
#                         if settings.DEBUG:
#                             form.add_error(None, f"{str(e)}")
#                         return render(request, template_name, context)
#
#                 shift.generate_shift_working_dates()
#                 return redirect(redirect_url, company_slug=company.slug)
#             except Exception as e:
#                 form.add_error(None, f"An unexpected error please try again:")
#                 if settings.DEBUG:
#                     form.add_error(None, f"{str(e)}")
#                 return render(request, template_name, context)
#
