from datetime import date, timedelta
from django.shortcuts import render, redirect
from .models import ShiftPattern


def retrieve_combined_shift_blocks(formset, shift_pattern, is_edit):
    unsaved_blocks = formset.save(commit=False)

    if not is_edit:
        return unsaved_blocks

    unsaved_blocks_not_in_db = [block for block in unsaved_blocks if block.id is None]
    unsaved_blocks_in_db = [block for block in unsaved_blocks if block.id is not None]

    updated_ids = [block.id for block in unsaved_blocks_in_db]

    saved_blocks = list(shift_pattern.blocks.exclude(id__in=updated_ids))

    sorted_existing_blocks = sorted(saved_blocks + unsaved_blocks_in_db, key=lambda b: b.id)

    combined_shift_blocks = sorted_existing_blocks + unsaved_blocks_not_in_db

    return combined_shift_blocks


def clear_shift_pattern_blocks_selected_days(shift_pattern):
    blocks = shift_pattern.blocks.all()
    for block in blocks:
        block.selected_days = []
        block.save()


def has_consistent_block_type(form, combined_shift_blocks):
    blocks_set = set()
    for block in combined_shift_blocks:
        if block.selected_days:
            blocks_set.add("selected_days")
        else:
            blocks_set.add("days_on_days_off")
    if len(blocks_set) > 1:
        form.add_error(None, "All blocks must have the same type.")
        return False
    return True


def is_duplicate_name(form, shift_pattern, is_edit=False):
    company = shift_pattern.company
    name = form.cleaned_data['name']

    if is_edit:
        if ShiftPattern.objects.filter(company=company, name=name).exclude(pk=shift_pattern.pk).exists():
            form.add_error('name', 'Shift pattern with this name already exists for your company.')
            return True
    else:
        if ShiftPattern.objects.filter(company=company, name=name).exists():
            form.add_error('name', 'Shift pattern with this name already exists for your company.')
            return True

    return False


def save_shift_blocks(formset, shift_pattern, combined_shift_blocks):
    order = 1
    for block in combined_shift_blocks:
        block.pattern = shift_pattern
        block.order = order
        order += 1
        block.save()
    formset.save_m2m()


def validate_days_on_off_in_shift_pattern(form, combined_shift_blocks):
    has_day_on = False
    has_days_off = False

    for block in combined_shift_blocks:

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


def validate_shift_pattern_start_date(form, shift_pattern, combined_shift_blocks):
    has_selected_days = True

    for block in combined_shift_blocks:
        if not block.selected_days:
            has_selected_days = False
            break

    if has_selected_days:
        start_date = shift_pattern.start_date
        if start_date.weekday() != 0:
            form.add_error('start_date', 'Start date must be a Monday.')
            return False
        return True


def handle_shift_pattern_post(request, form, formset, pk, template_name, redirect_url):
    render_parameters = {
        'request': request,
        'template_name': template_name,
        'context': {'form': form, 'formset': formset, }
    }

    if form.is_valid() and formset.is_valid():
        shift_pattern = form.save(commit=False)
        combined_shift_blocks = retrieve_combined_shift_blocks(formset, shift_pattern, is_edit=bool(pk))
        shift_pattern.company = request.user.get_company
        is_duplicate = is_duplicate_name(form, shift_pattern, is_edit=bool(pk))
        has_consistent = has_consistent_block_type(form, combined_shift_blocks)
        has_days_off = validate_days_on_off_in_shift_pattern(form, formset)
        check_start_date = validate_shift_pattern_start_date(form, shift_pattern, combined_shift_blocks)

        if is_duplicate or not has_consistent or not has_days_off or not check_start_date:
            return render(**render_parameters)

        shift_pattern.save()
        save_shift_blocks(formset, shift_pattern, combined_shift_blocks)
        shift_pattern.generate_shift_working_dates()
        return redirect(redirect_url)

    return render(**render_parameters)
