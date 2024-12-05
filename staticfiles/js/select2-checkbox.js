// $(document).ready(function() {
//     // Initialize Select2 with custom templates
//     $('.select2-checkbox').select2({
//         width: '100%',
//         closeOnSelect: false,
//         allowClear: true,
//         placeholder: 'Select items...',
//         templateResult: formatOption,
//         templateSelection: formatSelection,
//     });
//
//     // Format dropdown options
//     function formatOption(option) {
//         if (!option.id) return option.text; // Skip placeholder
//
//         var isSelected = option.selected ? 'checked' : '';
//         return $(
//             `<div class="option-container">
//                 <label class="checkbox-wrapper">
//                     <input type="checkbox" class="custom-checkbox" ${isSelected} />
//                     <span class="option-label">${option.text}</span>
//                 </label>
//             </div>`
//         );
//     }
//
//     // Format selected items display
//     function formatSelection(option) {
//         return option.text;
//     }
//
//     // Handle "Select All" functionality
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
//             // Add click handler for "Select All"
//             $selectAll.on('click', function() {
//                 var $select = $('.select2-checkbox');
//                 var allOptions = $select.find('option');
//                 var allValues = allOptions.map(function() {
//                     return this.value;
//                 }).get();
//
//                 if ($select.val()?.length === allValues.length) {
//                     $select.val([]).trigger('change'); // Deselect all
//                 } else {
//                     $select.val(allValues).trigger('change'); // Select all
//                 }
//
//                 // Update checkboxes
//                 $dropdown.find('.custom-checkbox').prop('checked', $select.val()?.length === allValues.length);
//             });
//         }
//     });
//
//     // Synchronize checkbox states
//     $('.select2-checkbox').on('change', function() {
//         var $dropdown = $('.select2-results');
//         var $options = $(this).find('option');
//         $options.each(function(index, option) {
//             var isChecked = $(option).is(':selected');
//             $dropdown.find(`.custom-checkbox:eq(${index})`).prop('checked', isChecked);
//         });
//
//         // Update "Select All" checkbox
//         var allSelected = $options.length === $(this).val()?.length;
//         $('.select-all-container .custom-checkbox').prop('checked', allSelected);
//     });
// });

// $(document).ready(function() {
//     // Initialize Select2
//     $('.select2-checkbox').select2({
//         width: '100%',
//         closeOnSelect: false,
//         allowClear: true,
//         placeholder: 'Select items...',
//         templateResult: formatOption,
//         templateSelection: formatSelection
//     });
//
//     function formatOption(option) {
//         if (!option.id) return option.text;
//
//         // Use the current selection state
//         const $select = $('.select2-checkbox');
//         const isSelected = $select.val()?.includes(option.id);
//
//         return $(`
//             <div class="option-container" data-value="${option.id}">
//                 <label class="checkbox-wrapper">
//                     <input type="checkbox" class="custom-checkbox" ${isSelected ? 'checked' : ''} />
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
//     // Add Select All option when dropdown opens
//     $('.select2-checkbox').on('select2:open', function() {
//         setTimeout(() => {
//             if (!$('.select-all-container').length) {
//                 const $dropdown = $('.select2-dropdown');
//                 const $select = $('.select2-checkbox');
//                 const allSelected = $select.find('option').length === $select.val()?.length;
//
//                 const $selectAll = $(`
//                     <div class="select-all-container">
//                         <label class="checkbox-wrapper">
//                             <input type="checkbox" id="select-all"
//                                    class="select-all-checkbox"
//                                    ${allSelected ? 'checked' : ''} />
//                             <span>Select All</span>
//                         </label>
//                     </div>
//                 `);
//
//                 $dropdown.prepend($selectAll);
//             }
//         }, 100);  // Increased timeout to ensure dropdown is ready
//     });
//
//     // Handle Select All
//     $(document).on('click', '#select-all', function(e) {
//         e.stopPropagation();
//         const $select = $('.select2-checkbox');
//         const allValues = $select.find('option').map(function() {
//             return this.value;
//         }).get();
//
//         if ($(this).is(':checked')) {
//             $select.val(allValues);
//         } else {
//             $select.val([]);
//         }
//
//         $select.trigger('change');
//
//         // Refresh the dropdown
//         setTimeout(() => {
//             $select.select2('close');
//             $select.select2('open');
//         }, 0);
//     });
//
//     // Handle individual checkbox clicks
//     $(document).on('click', '.select2-results .custom-checkbox', function(e) {
//         e.stopPropagation();
//         const $select = $('.select2-checkbox');
//         const value = $(this).closest('.option-container').data('value');
//         const currentValues = $select.val() || [];
//
//         if ($(this).is(':checked')) {
//             currentValues.push(value);
//         } else {
//             const index = currentValues.indexOf(value);
//             if (index > -1) currentValues.splice(index, 1);
//         }
//
//         $select.val(currentValues);
//         $select.trigger('change');
//     });
//
//     // Update checkboxes when selection changes
//     $('.select2-checkbox').on('change', function() {
//         const selectedValues = $(this).val() || [];
//
//         // Update Select All checkbox
//         $('#select-all').prop('checked',
//             selectedValues.length === $(this).find('option').length
//         );
//
//         // Force dropdown refresh
//         $(this).select2('close');
//         $(this).select2('open');
//     });
// });

$(document).ready(function() {
    $('.select2-checkbox').select2({
        width: '100%',
        closeOnSelect: false,
        allowClear: true,
        placeholder: 'Select items...',
        templateResult: formatOption,
        templateSelection: formatSelection
    });

    function formatOption(option) {
        if (!option.id) return option.text;

        const $select = $('.select2-checkbox');
        const isSelected = ($select.val() || []).includes(option.id);

        return $(`
            <div class="option-container" data-value="${option.id}">
                <input type="checkbox" 
                       class="custom-checkbox" 
                       ${isSelected ? 'checked' : ''}
                       onclick="event.stopPropagation()">
                <span class="option-label">${option.text}</span>
            </div>
        `);
    }

    function formatSelection(option) {
        return option.text;
    }

    $(document).on('click', '.select2-results .option-container', function(e) {
        const $checkbox = $(this).find('.custom-checkbox');
        const value = $(this).data('value');
        const $select = $('.select2-checkbox');
        let values = $select.val() || [];

        if ($checkbox.is(':checked')) {
            values = values.filter(v => v !== value);
            $checkbox.prop('checked', false);
        } else {
            values.push(value);
            $checkbox.prop('checked', true);
        }

        $select.val(values).trigger('change.select2', { keepOpen: true });
        e.preventDefault();
        e.stopPropagation();
    });

    $('.select2-checkbox').on('change', function(e, params) {
        if (params && params.keepOpen) {
            $('.select2-search__field').focus();
        }
    });
});