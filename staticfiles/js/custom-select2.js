// $(document).ready(function() {
//     $('.select2-checkbox').select2({
//         width: '100%',
//         closeOnSelect: false,
//         allowClear: true,
//         placeholder: 'Select items...',
//         templateResult: formatOption,
//         templateSelection: formatSelection,
//     });
//
//     function formatOption(option) {
//         if (!option.id) return option.text;
//         var isSelected = option.selected ? 'checked' : '';
//         return $(`
//             <div class="option-container">
//                 <label class="checkbox-wrapper">
//                     <input type="checkbox" class="custom-checkbox" ${isSelected} />
//                     <span class="option-label">${option.text}</span>
//                 </label>
//             </div>
//         `);
//     }
//
//     function formatSelection(option) {
//         return option.text;
//     }
//
//     $('.select2-checkbox').on('select2:open', function() {
//         if (!$('.select-all-container').length) {
//             var $dropdown = $('.select2-results');
//             var $selectAll = $(`
//                 <div class="select-all-container">
//                     <label class="checkbox-wrapper">
//                         <input type="checkbox" class="custom-checkbox" />
//                         <span class="option-label">Select All</span>
//                     </label>
//                 </div>
//             `);
//
//             $dropdown.prepend($selectAll);
//
//             $selectAll.on('click', function() {
//                 var $select = $('.select2-checkbox');
//                 var allOptions = $select.find('option');
//                 var allValues = allOptions.map(function() {
//                     return this.value;
//                 }).get();
//
//                 if ($select.val()?.length === allValues.length) {
//                     $select.val([]).trigger('change');
//                 } else {
//                     $select.val(allValues).trigger('change');
//                 }
//
//                 $dropdown.find('.custom-checkbox').prop('checked', $select.val()?.length === allValues.length);
//             });
//         }
//     });
//
//     $('.select2-checkbox').on('change', function() {
//         var $dropdown = $('.select2-results');
//         var $options = $(this).find('option');
//         $options.each(function(index, option) {
//             var isChecked = $(option).is(':selected');
//             $dropdown.find(`.custom-checkbox:eq(${index})`).prop('checked', isChecked);
//         });
//
//         var allSelected = $options.length === $(this).val()?.length;
//         $('.select-all-container .custom-checkbox').prop('checked', allSelected);
//     });
// });
$(document).ready(function () {
    const SELECTOR = '.select2-checkbox';

    // Initialize Select2
    $(SELECTOR).select2({
        width: '100%',
        closeOnSelect: false,
        allowClear: true,
        placeholder: 'Select items...',
        templateResult: formatOption,
        templateSelection: formatSelection,
    });

    // Template for dropdown options
    function formatOption(option) {
        if (!option.id) return option.text; // For placeholder or empty options
        const isSelected = $(option.element).is(':selected') ? 'checked' : '';
        return $(`
            <div class="option-container">
                <label class="checkbox-wrapper">
                    <input type="checkbox" class="custom-checkbox" data-value="${option.id}" ${isSelected} />
                    <span class="option-label">${option.text}</span>
                </label>
            </div>
        `);
    }

    // Template for selected items
    function formatSelection(option) {
        return option.text;
    }

    // Add "Select All" logic when the dropdown opens
    $(SELECTOR).on('select2:open', function () {
        const $dropdown = $('.select2-results__options');

        // Ensure "Select All" is added only once
        if (!$dropdown.find('.select-all-container').length) {
            const $selectAll = $(`
                <div class="select-all-container">
                    <label class="checkbox-wrapper">
                        <input type="checkbox" class="custom-checkbox select-all" />
                        <span class="option-label">Select All</span>
                    </label>
                </div>
            `);

            $dropdown.prepend($selectAll);

            // Handle "Select All" toggle
            $selectAll.find('.select-all').on('change', function () {
                const $select = $(SELECTOR);
                const allOptions = $select.find('option').map((_, opt) => opt.value).get();

                if ($(this).is(':checked')) {
                    $select.val(allOptions).trigger('change');
                } else {
                    $select.val([]).trigger('change');
                }

                updateCheckboxStates();
            });
        }

        updateCheckboxStates();
    });

    // Update checkboxes based on selected values
    function updateCheckboxStates() {
        const $select = $(SELECTOR);
        const selectedValues = $select.val() || [];
        const $dropdown = $('.select2-results__options');

        // Update individual checkboxes
        $dropdown.find('.custom-checkbox').not('.select-all').each(function () {
            const value = $(this).data('value');
            $(this).prop('checked', selectedValues.includes(value));
        });

        // Update "Select All" checkbox
        const allOptions = $select.find('option').map((_, opt) => opt.value).get();
        const allSelected = allOptions.every(value => selectedValues.includes(value));
        $dropdown.find('.select-all').prop('checked', allSelected);
    }

    // Handle individual checkbox clicks in the dropdown
    $(document).on('change', '.custom-checkbox:not(.select-all)', function () {
        const $checkbox = $(this);
        const value = $checkbox.data('value');
        const $select = $(SELECTOR);

        let selectedValues = $select.val() || [];

        if ($checkbox.is(':checked')) {
            if (!selectedValues.includes(value)) {
                selectedValues.push(value);
            }
        } else {
            selectedValues = selectedValues.filter(v => v !== value);
        }

        $select.val(selectedValues).trigger('change');
    });

    // Sync dropdown checkboxes when selection changes
    $(SELECTOR).on('change', updateCheckboxStates);
});
