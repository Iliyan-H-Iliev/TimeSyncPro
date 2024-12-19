from django.db import transaction
from django.shortcuts import render, redirect
from TimeSyncPro.companies.models import Team
from django.db.models import Max

from TimeSyncPro import settings
from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.shifts.models import ShiftBlock
from TimeSyncPro.shifts.tasks import generate_shift_working_dates_task


def has_consistent_block_type(form, formset):
    blocks_set = set()
    for block in formset:
        week_days = block.cleaned_data.get("week_days")
        if week_days:
            blocks_set.add("selected_days")
        else:
            blocks_set.add("days_on_days_off")
    if len(blocks_set) > 1:
        form.add_error(None, "All blocks must have the same type.")
        return False
    return True


def validate_days_on_off_in_shift(form, formset):
    has_day_on = False
    has_days_off = False

    for block in formset:

        if not block.instance.on_off_days:
            form.add_error(None, "Shift pattern must have days on and days off.")
            return False

        for day in block.instance.on_off_days:
            if day == 0:
                has_days_off = True
            else:
                has_day_on = True

            if has_day_on and has_days_off:
                break

        if has_day_on and has_days_off:
            break

    if not has_days_off or not has_day_on:
        form.add_error(None, "Shift pattern must have working days and rest days.")
        return False
    return True


def validate_shift_start_date(form, formset):
    has_selected_days = True

    for block in formset:
        selected_days = block.cleaned_data.get("week_days")
        if not selected_days:
            has_selected_days = False
            break

    if has_selected_days:
        start_date = form.cleaned_data.get("start_date")
        if start_date.weekday() != 0:
            form.add_error("start_date", "Start date must be a Monday.")
            return False
        return True
    return True


def delete_shift_blocks(shift, is_existing):
    if is_existing:
        shift.blocks.all().delete()


def clear_deleted_blocks(formset):
    new_forms = []
    for i, form in enumerate(formset):
        if hasattr(formset, "cleaned_data") and formset.cleaned_data[i].get(
            "DELETE", False
        ):
            continue  # Skip forms marked for deletion
        new_forms.append(form)
    return new_forms


def clean_formset(request, template_name, context, form, formset):
    has_consistent = has_consistent_block_type(form, formset)
    has_days_off = validate_days_on_off_in_shift(form, formset)
    check_start_date = validate_shift_start_date(form, formset)

    if not has_consistent or not has_days_off or not check_start_date:
        return render(request, template_name, context)


def save_shift_blocks(formset, shift):
    with transaction.atomic():

        blocks_to_create = []

        for index, form in enumerate(formset, start=1):
            if form.is_valid() and not form.cleaned_data.get("DELETE"):
                block = form.save(commit=False)
                block.pattern = shift
                block.order = index
                blocks_to_create.append(block)

        ShiftBlock.objects.bulk_create(blocks_to_create)


def save_shift_members(shift, form, is_existing=False):
    final_shift_members = set(form.cleaned_data.get("shift_members", []))

    if not is_existing:
        Profile.objects.filter(id__in=[m.id for m in final_shift_members]).update(
            shift=shift
        )

        return

    members_to_remove = form.initial_shift_members - final_shift_members
    Profile.objects.filter(id__in=[m.id for m in members_to_remove]).update(shift=None)

    members_to_add = final_shift_members - form.initial_shift_members
    Profile.objects.filter(id__in=[m.id for m in members_to_add]).update(shift=shift)


def save_shift_teams(shift, form, is_existing=False):
    final_shift_teams = set(form.cleaned_data.get("shift_teams", []))

    if not is_existing:
        Team.objects.filter(id__in=[t.id for t in final_shift_teams]).update(
            shift=shift
        )
        return

    teams_to_remove = form.initial_shift_teams - final_shift_teams
    Team.objects.filter(id__in=[t.id for t in teams_to_remove]).update(shift=None)

    teams_to_add = final_shift_teams - form.initial_shift_teams
    Team.objects.filter(id__in=[t.id for t in teams_to_add]).update(shift=shift)


def handle_shift_post(
    request,
    form,
    formset,
    pk,
    company,
    template_name,
    redirect_url,
    is_edit=False,
    *args,
    **kwargs,
):

    context = {
        "form": form,
        "formset": formset,
        "company_slug": company.slug,
        "pk": pk,
        "company": company,
    }

    obj = kwargs.get("obj", None)

    if obj:
        context["object"] = obj

    with transaction.atomic():
        try:

            with transaction.atomic():
                try:
                    is_existing = bool(pk)
                    shift = form.save(commit=False)
                    formset = clear_deleted_blocks(formset)
                    shift.company = company
                    clean_formset(request, template_name, context, form, formset)
                    delete_shift_blocks(shift, is_existing=is_existing)
                    shift.save()
                    save_shift_blocks(shift=shift, formset=formset)
                    save_shift_members(shift=shift, form=form, is_existing=is_existing)
                    save_shift_teams(shift=shift, form=form, is_existing=is_existing)
                    # shift.save()

                except Exception as e:
                    form.add_error(None, f"An unexpected error please try again:")
                    if settings.DEBUG:
                        form.add_error(None, f"{str(e)}")
                    return render(request, template_name, context)

            generate_shift_working_dates_task.delay(shift.id, is_edit=is_edit)

            return redirect(redirect_url, company_slug=company.slug)
        except Exception as e:
            if settings.DEBUG:
                form.add_error(None, f"{str(e)}")
            return render(request, template_name, context)
